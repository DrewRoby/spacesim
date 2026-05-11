## SimClient — autoload singleton that manages the TCP connection to the Rust sim.
##
## The Rust sim broadcasts newline-delimited JSON messages each tick.
## This autoload:
##   1. Connects to 127.0.0.1:7777 on startup (retries automatically)
##   2. Reads complete newline-terminated JSON messages from the stream
##   3. Parses them and emits typed signals for other nodes to consume
##
## Usage from any scene:
##   SimClient.market_updated.connect(_on_market_update)
##   SimClient.connected.connect(_on_connected)
##
## Message types (from Rust SimMessage enum):
##   {"type":"MarketUpdate", ...}    → market_updated(snapshot: Dictionary)
##   {"type":"WorldSnapshot", ...}   → world_snapshot(snapshot: Dictionary)
##   {"type":"EventFired", ...}      → event_fired(event: Dictionary)
##   {"type":"Pong"}                 → pong()

extends Node

# ── Signals ───────────────────────────────────────────────────────────────────

signal connected
signal disconnected
signal market_updated(snapshot: Dictionary)
signal world_snapshot(snapshot: Dictionary)
signal event_fired(event: Dictionary)
signal pong

# ── Configuration ─────────────────────────────────────────────────────────────

const SIM_HOST        := "127.0.0.1"
const SIM_PORT        := 7777
const RECONNECT_DELAY := 3.0   # seconds between reconnect attempts
const POLL_INTERVAL   := 0.05  # seconds between socket polls (50 ms ≈ 20 Hz)

# ── State ─────────────────────────────────────────────────────────────────────

var _socket:           StreamPeerTCP
var _connected:        bool = false
var _reconnect_timer:  float = 0.0
var _poll_timer:       float = 0.0
var _recv_buffer:      String = ""

# ── Lifecycle ─────────────────────────────────────────────────────────────────

func _ready() -> void:
	_socket = StreamPeerTCP.new()
	_try_connect()

func _process(delta: float) -> void:
	_poll_timer += delta
	if _poll_timer < POLL_INTERVAL:
		return
	_poll_timer = 0.0

	if not _connected:
		_reconnect_timer += POLL_INTERVAL
		if _reconnect_timer >= RECONNECT_DELAY:
			_reconnect_timer = 0.0
			_try_connect()
		return

	_socket.poll()

	match _socket.get_status():
		StreamPeerTCP.STATUS_CONNECTED:
			_drain_socket()
		StreamPeerTCP.STATUS_NONE, StreamPeerTCP.STATUS_ERROR:
			_on_disconnected()
		_:
			pass   # connecting — wait

# ── Connection management ─────────────────────────────────────────────────────

func _try_connect() -> void:
	_socket = StreamPeerTCP.new()
	var err := _socket.connect_to_host(SIM_HOST, SIM_PORT)
	if err == OK:
		# STATUS_CONNECTING — will move to STATUS_CONNECTED after polling
		_connected = false
	else:
		push_warning("SimClient: connect_to_host returned %d" % err)

func _on_disconnected() -> void:
	if _connected:
		_connected = false
		_recv_buffer = ""
		emit_signal("disconnected")
		push_warning("SimClient: disconnected from sim, will retry in %.1fs" % RECONNECT_DELAY)

# ── Reading ───────────────────────────────────────────────────────────────────

func _drain_socket() -> void:
	# Promote to connected state on first successful poll
	if not _connected:
		_connected = true
		emit_signal("connected")

	var available := _socket.get_available_bytes()
	if available <= 0:
		return

	# Read all available bytes, append to line buffer
	var raw: PackedByteArray = _socket.get_partial_data(available)[1]
	_recv_buffer += raw.get_string_from_utf8()

	# Process all complete newline-delimited messages
	while "\n" in _recv_buffer:
		var newline_pos := _recv_buffer.find("\n")
		var line        := _recv_buffer.substr(0, newline_pos).strip_edges()
		_recv_buffer     = _recv_buffer.substr(newline_pos + 1)

		if line.is_empty():
			continue

		_dispatch(line)

func _dispatch(json_str: String) -> void:
	var parsed := JSON.parse_string(json_str)
	if parsed == null or typeof(parsed) != TYPE_DICTIONARY:
		push_warning("SimClient: could not parse message: %s" % json_str.left(120))
		return

	var msg: Dictionary = parsed
	match msg.get("type", ""):
		"MarketUpdate":
			emit_signal("market_updated", msg)
		"WorldSnapshot":
			emit_signal("world_snapshot", msg)
		"EventFired":
			emit_signal("event_fired", msg)
		"Pong":
			emit_signal("pong")
		_:
			push_warning("SimClient: unknown message type: %s" % msg.get("type", "?"))

# ── Sending ───────────────────────────────────────────────────────────────────

func send_ping() -> void:
	_send_message({"type": "Ping"})

func send_trade_order(commodity_id: String, quantity: float, node_id: int = 0) -> void:
	_send_message({
		"type": "TradeOrder",
		"commodity_id": commodity_id,
		"quantity": quantity,
		"node_id": node_id,
	})

func _send_message(msg: Dictionary) -> void:
	if not _connected:
		push_warning("SimClient: cannot send — not connected")
		return
	var json := JSON.stringify(msg) + "\n"
	_socket.put_data(json.to_utf8_buffer())

# ── Status ────────────────────────────────────────────────────────────────────

func is_connected_to_sim() -> bool:
	return _connected
