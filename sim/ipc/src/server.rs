//! TCP IPC server — listens for Godot connections, dispatches messages.
//! stub
pub struct IpcServer;
impl IpcServer {
    pub async fn run(&self) -> anyhow::Result<()> {
        tracing::info!("IPC server stub — not yet implemented");
        Ok(())
    }
}
