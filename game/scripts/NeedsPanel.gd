## NeedsPanel — population need satiation bars.
##
## Shows the 7 biological needs as labeled progress bars, updated each tick.
## Satiation is reported as (mean, variance) from the Rust sim; we display
## the mean with a subtle variance indicator (opacity of the bar track).
##
## The sim doesn't currently broadcast satiation in MarketUpdate — we derive
## it from the demand signal as a proxy: high demand on a commodity ≈ low
## satiation on the need it primarily satisfies.
##
## A future WorldSnapshot message will carry explicit satiation state.

extends PanelContainer

@onready var _header: Label         = $VBox/Header
@onready var _bars:   VBoxContainer = $VBox/Bars

# need_id → primary commodity used as satiation proxy
const NEED_PROXY := {
	"hydration":     "water",
	"calories":      "grain",
	"protein":       "meat",
	"lipids":        "cooking_oil",
	"carbohydrates": "bread",
	"fiber":         "vegetables",
	"micronutrients":"fruit",
}

# Pretty display names
const NEED_NAMES := {
	"hydration":     "Hydration",
	"calories":      "Calories",
	"protein":       "Protein",
	"lipids":        "Lipids",
	"carbohydrates": "Carbohydrates",
	"fiber":         "Dietary Fiber",
	"micronutrients":"Micronutrients",
}

# need_id → {bar: ProgressBar, label: Label}
var _need_rows: Dictionary = {}

const COLOR_FULL    := Color(0.35, 0.88, 0.55)   # green — well-fed
const COLOR_PARTIAL := Color(1.0,  0.82, 0.30)   # yellow — some need
const COLOR_URGENT  := Color(1.0,  0.35, 0.35)   # red — urgent
const COLOR_DIM     := Color(0.55, 0.55, 0.55)

func _ready() -> void:
	SimClient.market_updated.connect(_on_market_updated)
	SimClient.connected.connect(_on_connected)
	_header.text = "POPULATION NEEDS"
	_build_rows()

func _on_connected() -> void:
	pass   # rows built at startup; will fill on first tick

func _build_rows() -> void:
	for need_id in NEED_PROXY.keys():
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 8)

		var lbl := Label.new()
		lbl.text = NEED_NAMES.get(need_id, need_id)
		lbl.custom_minimum_size = Vector2(130, 0)
		lbl.add_theme_color_override("font_color", Color(0.85, 0.85, 0.85))
		row.add_child(lbl)

		var bar := ProgressBar.new()
		bar.custom_minimum_size = Vector2(150, 16)
		bar.max_value = 1.0
		bar.value     = 0.5   # unknown until first tick
		bar.show_percentage = false
		row.add_child(bar)

		var val_lbl := Label.new()
		val_lbl.custom_minimum_size = Vector2(40, 0)
		val_lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
		val_lbl.add_theme_color_override("font_color", COLOR_DIM)
		row.add_child(val_lbl)

		_bars.add_child(row)
		_need_rows[need_id] = {"bar": bar, "label": val_lbl}

func _on_market_updated(snapshot: Dictionary) -> void:
	# Infer satiation proxy from demand: low demand ≈ high satiation
	var commodity_demand: Dictionary = {}
	for c in snapshot.get("commodities", []):
		commodity_demand[c.get("id", "")] = c.get("demand", 0.5)

	for need_id in NEED_PROXY.keys():
		var proxy_id: String = NEED_PROXY[need_id]
		var demand: float    = commodity_demand.get(proxy_id, 0.5)
		# Invert: high demand → low satiation proxy
		var satiation_proxy: float = clampf(1.0 - demand, 0.0, 1.0)

		var row: Dictionary = _need_rows.get(need_id, {})
		if row.is_empty():
			continue

		var bar: ProgressBar = row["bar"]
		var lbl: Label       = row["label"]

		bar.value = satiation_proxy
		lbl.text  = "%.2f" % satiation_proxy

		# Color the bar based on satiation level
		var bar_color: Color
		if satiation_proxy >= 0.7:
			bar_color = COLOR_FULL
		elif satiation_proxy >= 0.4:
			bar_color = COLOR_PARTIAL
		else:
			bar_color = COLOR_URGENT

		bar.add_theme_color_override("font_color", bar_color)
