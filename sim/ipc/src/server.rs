//! TCP IPC server — listens for Godot connections, broadcasts sim state each tick.
//!
//! Protocol: newline-delimited JSON. Each message is a complete JSON object
//! followed by '\n'. This is the simplest framing Godot's StreamPeerTCP can handle.
//!
//! Connection lifecycle:
//!   1. Godot connects to 127.0.0.1:7777 (configurable via IPC_PORT env var)
//!   2. Server sends a WorldSnapshot immediately on connect (current state)
//!   3. Each tick, server broadcasts MarketUpdate to all connected clients
//!   4. Clients may send ClientMessages (Ping, TradeOrder) at any time
//!   5. Server responds to Ping with Pong

use std::net::SocketAddr;
use std::sync::Arc;

use anyhow::Result;
use tokio::io::{AsyncBufReadExt, AsyncWriteExt, BufReader};
use tokio::net::{TcpListener, TcpStream};
use tokio::sync::{broadcast, Mutex};

use crate::protocol::{ClientMessage, SimMessage};

const DEFAULT_PORT: u16 = 7777;
const MAX_CLIENTS:  usize = 8;

// ── IpcServer ─────────────────────────────────────────────────────────────────

/// Shared broadcast channel for pushing sim messages to all connected clients.
pub type BroadcastTx = broadcast::Sender<String>;

pub struct IpcServer {
    port: u16,
    /// Broadcast sender — clone this to push messages from the tick loop.
    pub tx: BroadcastTx,
}

impl IpcServer {
    pub fn new() -> Self {
        let port = std::env::var("IPC_PORT")
            .ok()
            .and_then(|s| s.parse().ok())
            .unwrap_or(DEFAULT_PORT);

        let (tx, _) = broadcast::channel(64);
        IpcServer { port, tx }
    }

    /// Broadcast a SimMessage to all connected clients (non-blocking).
    /// Returns the number of active receivers at the time of send.
    pub fn broadcast(&self, msg: &SimMessage) -> usize {
        match serde_json::to_string(msg) {
            Ok(mut json) => {
                json.push('\n');   // newline delimiter for Godot's StreamPeerTCP
                self.tx.send(json).unwrap_or(0)
            }
            Err(e) => {
                tracing::warn!("IpcServer: failed to serialize message: {e}");
                0
            }
        }
    }

    /// Start the TCP listener. Spawns a task per client; returns immediately.
    /// The caller is responsible for running the tokio runtime.
    pub async fn run(self: Arc<Self>) -> Result<()> {
        let addr: SocketAddr = format!("127.0.0.1:{}", self.port).parse()?;
        let listener = TcpListener::bind(addr).await?;
        tracing::info!(port = self.port, "IPC server listening");

        let client_count = Arc::new(Mutex::new(0usize));

        loop {
            match listener.accept().await {
                Ok((stream, peer)) => {
                    let count = {
                        let mut c = client_count.lock().await;
                        *c += 1;
                        *c
                    };

                    if count > MAX_CLIENTS {
                        tracing::warn!(peer = %peer, "IPC: too many clients, dropping connection");
                        let mut c = client_count.lock().await;
                        *c -= 1;
                        continue;
                    }

                    tracing::info!(peer = %peer, clients = count, "IPC client connected");
                    let rx     = self.tx.subscribe();
                    let cc     = Arc::clone(&client_count);
                    tokio::spawn(async move {
                        if let Err(e) = handle_client(stream, peer, rx).await {
                            tracing::debug!(peer = %peer, "IPC client disconnected: {e}");
                        }
                        let mut c = cc.lock().await;
                        *c = c.saturating_sub(1);
                    });
                }
                Err(e) => tracing::error!("IPC accept error: {e}"),
            }
        }
    }
}

// ── Per-client handler ────────────────────────────────────────────────────────

async fn handle_client(
    stream:  TcpStream,
    peer:    SocketAddr,
    mut rx:  broadcast::Receiver<String>,
) -> Result<()> {
    let (read_half, mut write_half) = stream.into_split();
    let mut reader = BufReader::new(read_half);
    let mut line   = String::new();

    loop {
        tokio::select! {
            // Outbound: relay broadcast messages to this client
            msg = rx.recv() => {
                match msg {
                    Ok(json) => {
                        write_half.write_all(json.as_bytes()).await?;
                    }
                    Err(broadcast::error::RecvError::Lagged(n)) => {
                        tracing::warn!(peer = %peer, "IPC client lagged, dropped {n} messages");
                    }
                    Err(broadcast::error::RecvError::Closed) => break,
                }
            }

            // Inbound: parse client messages
            result = reader.read_line(&mut line) => {
                let n = result?;
                if n == 0 { break; }   // EOF — client disconnected

                let trimmed = line.trim();
                match serde_json::from_str::<ClientMessage>(trimmed) {
                    Ok(msg) => crate::handlers::handle(msg, &mut write_half).await?,
                    Err(e)  => tracing::debug!(peer = %peer, "IPC: bad message: {e}  raw={trimmed:?}"),
                }
                line.clear();
            }
        }
    }

    Ok(())
}
