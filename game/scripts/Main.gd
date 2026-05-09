## Main — root scene controller.
##
## Handles top-level layout and connection status indicator.
## The panels (MarketBoard, NeedsPanel) are children in the scene tree
## and receive data independently via SimClient signals.

extends Control

@onready var _status_bar:  Label = $VBox/StatusBar
@onready var _conn_dot:    Label = $VBox/StatusBar/ConnDot

const COLOR_CONNECTED    := Color(0.35, 0.95, 0.55)
const COLOR_DISCONNECTED := Color(1.0,  0.35, 0.35)
const COLOR_DIM          := Color(0.55, 0.55, 0.55)

func _ready() -> void:
	SimClient.connected.connect(_on_connected)
	SimClient.disconnected.connect(_on_disconnected)
	SimClient.market_updated.connect(_on_market_updated)
	_set_status(false, "Connecting to sim on 127.0.0.1:7777…")

func _on_connected() -> void:
	_set_status(true, "Connected — sim running")

func _on_disconnected() -> void:
	_set_status(false, "Sim disconnected — retrying…")

func _on_market_updated(snapshot: Dictionary) -> void:
	var tick: int = snapshot.get("tick", 0)
	_set_status(true, "Tick %d  ·  Week %d" % [tick, tick])

func _set_status(connected: bool, text: String) -> void:
	if _conn_dot:
		_conn_dot.text = "●"
		_conn_dot.add_theme_color_override(
			"font_color",
			COLOR_CONNECTED if connected else COLOR_DISCONNECTED
		)
	if _status_bar:
		# The label after the dot
		var lbl: Label = _status_bar.get_node_or_null("StatusText")
		if lbl:
			lbl.text = text
