//! spacesim-ipc — local IPC server bridging the Rust sim and Godot frontend.
//!
//! Godot connects as a TCP client. The server receives PlayerAction messages
//! and broadcasts WorldSnapshot + MarketUpdate + EventFired messages each tick.

pub mod server;
pub mod protocol;
pub mod handlers;

pub use server::IpcServer;
