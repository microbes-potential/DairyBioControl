from dash import html

PALETTES = {
    "Safety": ["#E53935","#C62828","#FF7043","#8E24AA","#B71C1C","#FF8A65","#D84315","#6D4C41","#EF5350","#AD1457"],
    "DairyAdaptation": ["#1E88E5","#1976D2","#64B5F6","#1565C0","#42A5F5","#0D47A1","#90CAF9","#039BE5","#00ACC1","#26C6DA"],
    "Antibacterial": ["#43A047","#2E7D32","#66BB6A","#1B5E20","#9CCC65","#00ACC1","#00897B","#26A69A","#7CB342","#558B2F"],
    "Antifungal": ["#6D4C41","#8D6E63","#A1887F","#5D4037","#795548","#4E342E","#BCAAA4","#3E2723","#8E24AA","#6A1B9A"],
    "Default": ["#3366CC","#DC3912","#FF9900","#109618","#990099","#0099C6","#DD4477","#66AA00","#B82E2E","#316395","#994499","#22AA99"]
}
GRAPH_CONFIG = {"displaylogo": False,
    "toImageButtonOptions": {"format":"png","filename":"dairybiochart","height":800,"width":1600,"scale":4},
    "modeBarButtonsToRemove": ["select2d","lasso2d","autoScale2d"]}

def module_palette(cat): return PALETTES.get(cat, PALETTES["Default"])

def info_banner(children):
    return html.Div(children, style={
        "background":"#eef5ff","border":"1px solid #cfe0ff","color":"#345",
        "padding":"10px 12px","borderRadius":"8px","margin":"6px 0 16px 0","fontSize":"15px"})

