import pandas as pd
import plotly.express as px
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc

# 1. Chargement des données
df = pd.read_csv("supermarket_sales.csv")

villes = df["City"].unique()
sexes = df["Gender"].unique()


# 2. DÉFINITION DES COULEURS ET DES STYLES

COLORS = {
    "background": "#F5F7FB",
    "card": "#FFFFFF",
    "card_alt": "#EEF2F7",
    "border": "#D9E2EC",
    "text": "#1F2937",
    "muted": "#6B7280",
    "primary": "#06897C",
    "primary_hover": "#115E59",
    "secondary": "#2563EB",
    "success": "#10B981",
    "warning": "#F59E0B",
    "danger": "#DC2626",
    "grid": "#E5E7EB",
    "chart": ["#0F766E",  "#F59E0B", "#3562BC", "#51267F", "#29395A", "#3A583C"]
}

APP_STYLE = {
    "backgroundColor": COLORS["background"],
    "minHeight": "100vh",
    "padding": "24px",
    "fontFamily": "Arial, sans-serif",
    "color": COLORS["text"]
}

CARD_STYLE = {
    "backgroundColor": COLORS["card"],
    "border": f"1px solid {COLORS['border']}",
    "borderRadius": "16px",
    "padding": "18px",
    "boxShadow": "0 2px 8px rgba(15, 23, 42, 0.05)"
}

FILTER_BOX_STYLE = {
    "backgroundColor": COLORS["card"],
    "border": f"1px solid {COLORS['border']}",
    "borderRadius": "14px",
    "padding": "18px 14px",
    "marginBottom": "20px",
    "display": "flex",
    "justifyContent": "space-between"
}

KPI_TITLE_STYLE = {
    "color": COLORS["muted"],
    "fontSize": "15px",
    "marginBottom": "6px",
    "textTransform": "uppercase",
    "fontWeight": "bold"
}

KPI_VALUE_STYLE = {
    "fontSize": "28px",
    "fontWeight": "700"
}

TITLE_STYLE = {
    "color": COLORS["text"],
    "fontSize": "32px",
    "fontWeight": "700",
    "marginBottom": "20px",
    "textAlign": "center"
}

# 3. Création de l'application
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server

# 4. Interface du tableau de bord (Layout)
app.layout = html.Div([
    html.H1("Tableau de bord des ventes du supermarché", style=TITLE_STYLE),

    # Première ligne : Les filtres
    html.Div([
        html.Div([
            dcc.Dropdown(
                id="gender-dropdown",
                options=[{'label': sexe, 'value': sexe} for sexe in sexes],
                value=None,
                placeholder="Choisir un sexe"
            )
        ], style={"width": "48%"}),

        html.Div([
            dcc.Dropdown(
                id="city-dropdown",
                options=[{'label': ville, 'value': ville} for ville in villes],
                value=None,
                placeholder="Choisir une ville"
            )
        ], style={"width": "48%"})
    ], style=FILTER_BOX_STYLE),

    # Espace pour les indicateurs
    html.Div(id="kpi-container", style={"display": "flex", "justifyContent": "space-between", "marginBottom": "20px"}),

    # Espaces pour les graphiques
    html.Div(dcc.Graph(id="lines-total-achat"), style={**CARD_STYLE, "marginBottom": "20px"}),
    
    dbc.Row([
        dbc.Col(html.Div(dcc.Graph(id="pie-product-line"), style=CARD_STYLE), md=6),
        dbc.Col(html.Div(dcc.Graph(id="bar-nombre-total-achat"), style=CARD_STYLE), md=6)
    ])
    
], style=APP_STYLE)


# 5. Callback interactif pour MAJ Globale
@app.callback(
    [Output('kpi-container', 'children'),
     Output('lines-total-achat', 'figure'),
     Output('pie-product-line', 'figure'),
     Output('bar-nombre-total-achat', 'figure')],
    [Input('gender-dropdown', 'value'),
     Input('city-dropdown', 'value')]
)
def update_dashboard(selected_gender, selected_city):
    # La copie locale du dataframe pour ne pas altérer les données de base
    dff = df.copy()

    # Filtrage selon les choix de l'utilisateur
    if selected_gender is not None:
        dff = dff[dff["Gender"] == selected_gender]
    if selected_city is not None:
        dff = dff[dff["City"] == selected_city]

    # --- INDICATEURS ---
    montant_total = dff["Total"].sum()
    nombre_achats = dff["Invoice ID"].count()
    
    kpis_html = [
        html.Div([
            html.Div("Montant total", style=KPI_TITLE_STYLE),
            html.Div(f"{montant_total:.2f} $", style={**KPI_VALUE_STYLE, "color": COLORS["primary"]})
        ], style={**CARD_STYLE, "width": "48%", "textAlign": "center"}),
        
        html.Div([
            html.Div("Nombre d'achats", style=KPI_TITLE_STYLE),
            html.Div(f"{nombre_achats}", style={**KPI_VALUE_STYLE, "color": COLORS["primary"]})
        ], style={**CARD_STYLE, "width": "48%", "textAlign": "center"})
    ]

    # --- GRAPHIQUES ---
    dff['Date'] = pd.to_datetime(dff['Date'])
    
    # 1. Évolution dans le temps 
    evol_dans_le_temps = dff.groupby('Date')['Total'].sum().reset_index().sort_values('Date')
    fig_ligne = px.line(
        evol_dans_le_temps, x='Date', y='Total', 
        title="<b>Évolution des achats dans le temps</b>",
        color_discrete_sequence=[COLORS["primary_hover"]]
    )
    
    # 2. Répartition par catégorie 
    df_pie = dff.groupby("Product line")["Total"].sum().reset_index()
    fig_pie = px.pie(
        df_pie, names="Product line", values="Total", 
        title="<b>Ventes par Catégorie de Produit</b>", 
        hole=0.45, 
        color_discrete_sequence=COLORS["chart"]
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent')

    # 3. Nombre d'achats par catégorie 
    achats_par_produit = dff.groupby("Product line")["Invoice ID"].count().reset_index()
    fig_bar = px.bar(
        achats_par_produit, x="Product line", y="Invoice ID", 
        title="<b>Nombre total d'achats par catégorie</b>", 
        labels={"Product line": "Product Category", "Invoice ID": "Number of Purchases"},
        color_discrete_sequence=[COLORS["secondary"]]
    )

    # Mise à jour des styles communs aux graphiques 
    for fig in [fig_ligne, fig_pie, fig_bar]:
        fig.update_layout(
            paper_bgcolor="rgba(0,0,0,0)", 
            plot_bgcolor="rgba(0,0,0,0)",
            font_color=COLORS["text"]
        )
        fig.update_xaxes(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"])
        fig.update_yaxes(gridcolor=COLORS["grid"], zerolinecolor=COLORS["grid"])

    # On retourne les éléments à afficher dans l'ordre de la liste des Outputs
    return kpis_html, fig_ligne, fig_pie, fig_bar


# 6. Lancement du serveur
if __name__ == '__main__':
    app.run(debug=True, port=8050)
