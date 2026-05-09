## MarketBoard — live commodity price table.
##
## Displays a scrollable table of all commodities with:
##   - Current price (color-coded: red > 1.5, yellow > 1.1, cyan < 0.7)
##   - Price trend arrow (▲ / ▼ / —)
##   - Demand bar
##   - Supply value
##
## Receives data via the market_updated signal from SimClient autoload.

extends PanelContainer

# ── Scene references (set in Main.tscn) ──────────────────────────────────────

@onready var _header_label: Label       = $VBox/Header
@onready var _tick_label:   Label       = $VBox/TickRow/TickLabel
@onready var _table:        VBoxContainer = $VBox/Scroll/Table

# ── Internal state ────────────────────────────────────────────────────────────

# commodity_id → Dictionary of last known values
var _prev: Dictionary = {}

# commodity_id → Control row node
var _rows: Dictionary = {}

# Price thresholds
const PRICE_HIGH   := 1.50
const PRICE_WARN   := 1.10
const PRICE_LOW    := 0.70

const COLOR_HIGH   := Color(1.0, 0.35, 0.35)   # red
const COLOR_WARN   := Color(1.0, 0.82, 0.30)   # yellow
const COLOR_LOW    := Color(0.35, 0.88, 0.95)   # cyan
const COLOR_NORMAL := Color(0.55, 0.95, 0.55)   # green
const COLOR_DIM    := Color(0.55, 0.55, 0.55)

# ── Lifecycle ─────────────────────────────────────────────────────────────────

func _ready() -> void:
	SimClient.market_updated.connect(_on_market_updated)
	SimClient.connected.connect(_on_connected)
	SimClient.disconnected.connect(_on_disconnected)
	_header_label.text = "COMMODITIES"
	_set_status("Waiting for sim…")

func _on_connected() -> void:
	_set_status("Connected — waiting for first tick")

func _on_disconnected() -> void:
	_set_status("⚠  Disconnected — retrying…")

# ── Data update ───────────────────────────────────────────────────────────────

func _on_market_updated(snapshot: Dictionary) -> void:
	var tick: int = snapshot.get("tick", 0)
	_tick_label.text = "Week %d  (day %d)" % [tick, (tick - 1) * 7 + 1]

	var commodities: Array = snapshot.get("commodities", [])

	# Sort by demand descending
	commodities.sort_custom(func(a, b): return a.get("demand", 0.0) > b.get("demand", 0.0))

	for c in commodities:
		var cid: String  = c.get("id", "?")
		var price: float = c.get("price", 1.0)
		var demand: float = c.get("demand", 0.0)
		var supply: float = c.get("supply", 0.0)
		var prev_price: float = _prev.get(cid, {}).get("price", price)

		if not _rows.has(cid):
			_rows[cid] = _make_row(cid)
			_table.add_child(_rows[cid])

		_update_row(_rows[cid], cid, price, demand, supply, prev_price)
		_prev[cid] = {"price": price, "demand": demand, "supply": supply}

# ── Row creation ──────────────────────────────────────────────────────────────

func _make_row(cid: String) -> HBoxContainer:
	var row := HBoxContainer.new()
	row.name = "row_" + cid
	row.add_theme_constant_override("separation", 8)

	var name_lbl := Label.new()
	name_lbl.name = "Name"
	name_lbl.text = cid.replace("_", " ")
	name_lbl.custom_minimum_size = Vector2(140, 0)
	name_lbl.add_theme_color_override("font_color", Color(0.85, 0.85, 0.85))
	row.add_child(name_lbl)

	var price_lbl := Label.new()
	price_lbl.name = "Price"
	price_lbl.custom_minimum_size = Vector2(56, 0)
	price_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	row.add_child(price_lbl)

	var arrow_lbl := Label.new()
	arrow_lbl.name = "Arrow"
	arrow_lbl.custom_minimum_size = Vector2(20, 0)
	arrow_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	row.add_child(arrow_lbl)

	var demand_bar := ProgressBar.new()
	demand_bar.name = "DemandBar"
	demand_bar.custom_minimum_size = Vector2(100, 14)
	demand_bar.max_value = 1.0
	demand_bar.show_percentage = false
	row.add_child(demand_bar)

	var supply_lbl := Label.new()
	supply_lbl.name = "Supply"
	supply_lbl.custom_minimum_size = Vector2(48, 0)
	supply_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	supply_lbl.add_theme_color_override("font_color", COLOR_DIM)
	row.add_child(supply_lbl)

	return row

func _update_row(
	row: HBoxContainer,
	_cid: String,
	price: float,
	demand: float,
	supply: float,
	prev_price: float,
) -> void:
	var price_lbl: Label      = row.get_node("Price")
	var arrow_lbl: Label      = row.get_node("Arrow")
	var demand_bar: ProgressBar = row.get_node("DemandBar")
	var supply_lbl: Label     = row.get_node("Supply")

	# Price
	price_lbl.text = "%.3f" % price
	var col := _price_color(price)
	price_lbl.add_theme_color_override("font_color", col)

	# Arrow
	if price > prev_price * 1.01:
		arrow_lbl.text = "▲"
		arrow_lbl.add_theme_color_override("font_color", COLOR_HIGH)
	elif price < prev_price * 0.99:
		arrow_lbl.text = "▼"
		arrow_lbl.add_theme_color_override("font_color", COLOR_LOW)
	else:
		arrow_lbl.text = "—"
		arrow_lbl.add_theme_color_override("font_color", COLOR_DIM)

	# Demand bar
	demand_bar.value = demand

	# Supply
	supply_lbl.text = "%.3f" % supply

func _price_color(price: float) -> Color:
	if price > PRICE_HIGH: return COLOR_HIGH
	if price > PRICE_WARN: return COLOR_WARN
	if price < PRICE_LOW:  return COLOR_LOW
	return COLOR_NORMAL

# ── Helpers ───────────────────────────────────────────────────────────────────

func _set_status(text: String) -> void:
	if _tick_label:
		_tick_label.text = text
