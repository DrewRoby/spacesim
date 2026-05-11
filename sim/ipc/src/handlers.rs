//! Per-message-type handler functions called from the per-client task.

use anyhow::Result;
use tokio::io::AsyncWriteExt;
use tokio::net::tcp::OwnedWriteHalf;

use crate::protocol::{ClientMessage, SimMessage};

/// Dispatch a ClientMessage and write any immediate response to the client.
pub async fn handle(msg: ClientMessage, out: &mut OwnedWriteHalf) -> Result<()> {
    match msg {
        ClientMessage::Ping => {
            let pong = serde_json::to_string(&SimMessage::Pong)? + "\n";
            out.write_all(pong.as_bytes()).await?;
            tracing::debug!("IPC: Ping → Pong");
        }
        ClientMessage::TradeOrder(order) => {
            // Trade orders will be queued into the world state in a future tick.
            // For now we just log them so the Godot client can see they arrive.
            tracing::info!(
                commodity = %order.commodity_id,
                quantity  = order.quantity,
                node      = order.node_id,
                "IPC: TradeOrder received"
            );
        }
    }
    Ok(())
}
