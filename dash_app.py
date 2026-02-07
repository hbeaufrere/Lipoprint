"""Gel Densitometry Analysis - Plotly Dash App with Interactive Dragging

This app provides interactive drag-to-adjust band boundaries on graphs.
Uses Dash for full interactivity with Plotly visualizations.
"""

import dash
from dash import dcc, html, callback, Input, Output, State
import dash_bootstrap_components as dbc
import plotly.graph_objects as go
import numpy as np
import pandas as pd
import base64
import io
from pathlib import Path

from image_processor import GelImageProcessor, DensitometryAnalyzer
from export_handler import AnalysisExporter

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "Gel Densitometry Analysis"

# Color scheme
COLORS = {
    'VLDL': '#FFD700',  # Yellow
    'IDL': '#FF8C00',   # Orange
    'LDL': '#FF0000',   # Red
    'HDL': '#4ECDC4'    # Teal
}

# ============================================================================
# APP LAYOUT
# ============================================================================

app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("🧬 Gel Electrophoresis Densitometry Analysis",
                   className="mb-4 mt-4 text-center text-primary")
        ])
    ]),

    dbc.Row([
        # LEFT COLUMN - Controls
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Controls", className="card-title"),

                    # File upload
                    dcc.Upload(
                        id='upload-image',
                        children=html.Div([
                            'Drag and drop or ',
                            html.A('select a gel image')
                        ]),
                        style={
                            'width': '100%',
                            'height': '60px',
                            'lineHeight': '60px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center',
                            'margin': '10px 0'
                        },
                        multiple=False
                    ),

                    html.Hr(),

                    # Tube selection
                    html.Label("Tube Selection:", className="fw-bold"),
                    dcc.Dropdown(
                        id='tube-selector',
                        options=[{'label': f'Tube {i+1}', 'value': i} for i in range(12)],
                        value=0,
                        disabled=True
                    ),

                    html.Hr(),

                    # Band limit sliders
                    html.Label("Band Limits (pixels):", className="fw-bold"),
                    html.Br(),

                    html.Label("VLDL:", className="fw-bold text-danger"),
                    dbc.Row([
                        dbc.Col([
                            dcc.RangeSlider(
                                id='vldl-slider',
                                min=0, max=313, step=1,
                                value=[27, 48],
                                marks={0: '0', 313: '313'},
                                disabled=True,
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ], width=9),
                        dbc.Col([
                            dbc.InputGroup([
                                dcc.Input(
                                    id='vldl-min-input',
                                    type='number',
                                    min=0, max=313,
                                    value=27,
                                    disabled=True,
                                    className='form-control form-control-sm',
                                    placeholder='Min',
                                    style={'font-size': '12px', 'padding': '2px 5px', 'width': '45px'}
                                ),
                                dcc.Input(
                                    id='vldl-max-input',
                                    type='number',
                                    min=0, max=313,
                                    value=48,
                                    disabled=True,
                                    className='form-control form-control-sm',
                                    placeholder='Max',
                                    style={'font-size': '12px', 'padding': '2px 5px', 'width': '45px'}
                                ),
                            ], size='sm')
                        ], width=3),
                    ], className="mb-3"),

                    html.Label("IDL:", className="fw-bold text-warning"),
                    dbc.Row([
                        dbc.Col([
                            dcc.RangeSlider(
                                id='idl-slider',
                                min=0, max=313, step=1,
                                value=[48, 65],
                                marks={0: '0', 313: '313'},
                                disabled=True,
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ], width=9),
                        dbc.Col([
                            dbc.InputGroup([
                                dcc.Input(
                                    id='idl-min-input',
                                    type='number',
                                    min=0, max=313,
                                    value=48,
                                    disabled=True,
                                    className='form-control form-control-sm',
                                    placeholder='Min',
                                    style={'font-size': '12px', 'padding': '2px 5px', 'width': '45px'}
                                ),
                                dcc.Input(
                                    id='idl-max-input',
                                    type='number',
                                    min=0, max=313,
                                    value=65,
                                    disabled=True,
                                    className='form-control form-control-sm',
                                    placeholder='Max',
                                    style={'font-size': '12px', 'padding': '2px 5px', 'width': '45px'}
                                ),
                            ], size='sm')
                        ], width=3),
                    ], className="mb-3"),

                    html.Label("LDL:", className="fw-bold text-warning"),
                    dbc.Row([
                        dbc.Col([
                            dcc.RangeSlider(
                                id='ldl-slider',
                                min=0, max=313, step=1,
                                value=[68, 120],
                                marks={0: '0', 313: '313'},
                                disabled=True,
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ], width=9),
                        dbc.Col([
                            dbc.InputGroup([
                                dcc.Input(
                                    id='ldl-min-input',
                                    type='number',
                                    min=0, max=313,
                                    value=68,
                                    disabled=True,
                                    className='form-control form-control-sm',
                                    placeholder='Min',
                                    style={'font-size': '12px', 'padding': '2px 5px', 'width': '45px'}
                                ),
                                dcc.Input(
                                    id='ldl-max-input',
                                    type='number',
                                    min=0, max=313,
                                    value=120,
                                    disabled=True,
                                    className='form-control form-control-sm',
                                    placeholder='Max',
                                    style={'font-size': '12px', 'padding': '2px 5px', 'width': '45px'}
                                ),
                            ], size='sm')
                        ], width=3),
                    ], className="mb-3"),

                    html.Label("HDL:", className="fw-bold text-info"),
                    dbc.Row([
                        dbc.Col([
                            dcc.RangeSlider(
                                id='hdl-slider',
                                min=0, max=313, step=1,
                                value=[260, 300],
                                marks={0: '0', 313: '313'},
                                disabled=True,
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ], width=9),
                        dbc.Col([
                            dbc.InputGroup([
                                dcc.Input(
                                    id='hdl-min-input',
                                    type='number',
                                    min=0, max=313,
                                    value=260,
                                    disabled=True,
                                    className='form-control form-control-sm',
                                    placeholder='Min',
                                    style={'font-size': '12px', 'padding': '2px 5px', 'width': '45px'}
                                ),
                                dcc.Input(
                                    id='hdl-max-input',
                                    type='number',
                                    min=0, max=313,
                                    value=300,
                                    disabled=True,
                                    className='form-control form-control-sm',
                                    placeholder='Max',
                                    style={'font-size': '12px', 'padding': '2px 5px', 'width': '45px'}
                                ),
                            ], size='sm')
                        ], width=3),
                    ], className="mb-3"),

                    html.Hr(),

                    # Reference Tubes Thumbnail
                    html.Label("Tube Reference:", className="fw-bold text-muted"),
                    html.Div(id='reference-tubes', style={'text-align': 'center', 'margin-top': '10px'})

                ])
            ])
        ], width=3),

        # RIGHT COLUMN - Results
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("Analysis", className="card-title"),

                    # Densitometry Profile Graph
                    dcc.Graph(
                        id='profile-graph',
                        style={'height': '500px'}
                    ),

                    html.Hr(),

                    # Gel Image
                    dcc.Graph(
                        id='gel-graph',
                        style={'height': '350px'}
                    ),

                    html.Hr(),

                    # Results Table
                    html.Label("Lipoprotein Profile (%):", className="fw-bold"),
                    html.Div(id='results-table'),

                    html.Br(),

                    # Metrics
                    dbc.Row(id='metrics-row'),

                    html.Hr(),

                    # Export Buttons
                    html.Label("Export:", className="fw-bold"),
                    dbc.Row([
                        dbc.Col([
                            dcc.Download(id='download-csv'),
                            dbc.Button("📥 CSV", id='export-csv-btn', color="primary", size="sm", className="w-100")
                        ], className="mb-2"),
                        dbc.Col([
                            dcc.Download(id='download-json'),
                            dbc.Button("📥 JSON", id='export-json-btn', color="primary", size="sm", className="w-100")
                        ], className="mb-2"),
                        dbc.Col([
                            dcc.Download(id='download-txt'),
                            dbc.Button("📥 Summary", id='export-txt-btn', color="primary", size="sm", className="w-100")
                        ], className="mb-2"),
                    ]),

                ])
            ])
        ], width=9),
    ]),

    # Hidden stores for state management
    dcc.Store(id='processor-store', storage_type='memory'),
    dcc.Store(id='analyzer-store', storage_type='memory'),

], fluid=True, className="p-4")


# ============================================================================
# CALLBACKS
# ============================================================================

@callback(
    Output('processor-store', 'data'),
    Input('upload-image', 'contents'),
    prevent_initial_call=True
)
def load_image(contents):
    """Load and process uploaded image"""
    if not contents:
        return None

    try:
        # Decode uploaded file
        content_type, content_string = contents.split(',')
        decoded = base64.b64decode(content_string)

        # Create temporary file
        import tempfile
        with tempfile.NamedTemporaryFile(suffix='.tif', delete=False) as tmp:
            tmp.write(decoded)
            tmp_path = tmp.name

        # Process image
        processor = GelImageProcessor(tmp_path)
        lipoware_roi = (52, 353, 650, 313)
        processor.extract_tubes(num_tubes=12, tubes_per_row=20, roi=lipoware_roi)

        # Serialize to JSON-compatible format
        tubes_data = []
        for tube in processor.tubes:
            tubes_data.append({
                'index': int(tube['index']),
                'region': tube['region'].tolist(),
                'x_range': [int(x) for x in tube['x_range']],
                'y_range': [int(y) for y in tube['y_range']],
            })

        return {
            'image_path': tmp_path,
            'tubes_count': len(processor.tubes),
            'tubes': tubes_data
        }
    except Exception as e:
        print(f"Error loading image: {e}")
        return None


@callback(
    [Output('tube-selector', 'disabled'),
     Output('vldl-slider', 'disabled'),
     Output('idl-slider', 'disabled'),
     Output('ldl-slider', 'disabled'),
     Output('hdl-slider', 'disabled')],
    Input('processor-store', 'data')
)
def enable_controls(processor_data):
    """Enable controls when image is loaded"""
    enabled = processor_data is not None
    return [not enabled] * 5


@callback(
    Output('reference-tubes', 'children'),
    Input('processor-store', 'data')
)
def display_reference_tubes(processor_data):
    """Display all 12 tubes as reference grid"""
    if not processor_data:
        return html.Div("Load image to see reference", className="text-muted small")

    try:
        tubes_data = processor_data['tubes']
        if not tubes_data:
            return html.Div("No tubes found", className="text-muted small")

        # Get tube images and rotate them
        tube_images = []
        for tube_data in tubes_data:
            region = np.array(tube_data['region'], dtype=np.uint8)
            rotated = np.rot90(region)  # Rotate for horizontal view
            tube_images.append(rotated)

        # Find max dimensions for padding
        max_height = max(t.shape[0] for t in tube_images)
        max_width = max(t.shape[1] for t in tube_images)

        # Pad all tubes to same size
        padded_tubes = []
        for t in tube_images:
            h, w = t.shape
            pad_h = (max_height - h) // 2
            pad_w = (max_width - w) // 2
            padded = np.pad(t, ((pad_h, max_height - h - pad_h), (pad_w, max_width - w - pad_w)),
                           mode='constant', constant_values=255)
            padded_tubes.append(padded)

        # Create 3x4 grid (3 rows, 4 columns)
        rows = []
        for i in range(0, 12, 4):
            row = np.hstack(padded_tubes[i:i+4])
            rows.append(row)
        montage = np.vstack(rows)

        # Encode to base64
        import io
        from PIL import Image
        img_pil = Image.fromarray(montage.astype(np.uint8))
        buf = io.BytesIO()
        img_pil.save(buf, format='PNG')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.getvalue()).decode()

        return html.Img(
            src=f'data:image/png;base64,{img_base64}',
            style={'width': '100%', 'max-width': '280px', 'border': '1px solid #ddd', 'border-radius': '4px'}
        )
    except Exception as e:
        return html.Div(f"Error: {str(e)}", className="text-danger small")


@callback(
    [Output('profile-graph', 'figure'),
     Output('gel-graph', 'figure'),
     Output('results-table', 'children'),
     Output('metrics-row', 'children')],
    [Input('tube-selector', 'value'),
     Input('vldl-slider', 'value'),
     Input('idl-slider', 'value'),
     Input('ldl-slider', 'value'),
     Input('hdl-slider', 'value'),
     Input('processor-store', 'data')],
    prevent_initial_call=True
)
def update_analysis(tube_idx, vldl, idl, ldl, hdl, processor_data):
    """Update all visualizations and results"""

    if not processor_data:
        return {}, {}, "Load an image to start", []

    # Reconstruct processor
    processor = GelImageProcessor.__new__(GelImageProcessor)
    processor.image_path = processor_data['image_path']
    processor.tubes = []

    # Reconstruct tubes
    import cv2
    for tube_data in processor_data['tubes']:
        region = np.array(tube_data['region'], dtype=np.uint8)
        processor.tubes.append({
            'index': tube_data['index'],
            'region': region,
            'x_range': tuple(tube_data['x_range']),
            'y_range': tuple(tube_data['y_range']),
        })

    # Get profile
    profile = processor.get_densitometry_profile(tube_idx, auto_crop=False)
    background = processor.detect_background(profile)
    profile_len = len(profile)

    # Create bands
    bands = [
        {'left': vldl[0], 'right': vldl[1], 'category': 'VLDL'},
        {'left': idl[0], 'right': idl[1], 'category': 'IDL'},
        {'left': ldl[0], 'right': ldl[1], 'category': 'LDL'},
        {'left': hdl[0], 'right': hdl[1], 'category': 'HDL'},
    ]

    analyzer = DensitometryAnalyzer(profile, background)
    analyzer.bands = bands

    # ---- Create Profile Graph ----
    x = np.arange(len(profile))

    fig_profile = go.Figure()

    # Profile line
    fig_profile.add_trace(go.Scatter(
        x=x, y=profile,
        mode='lines',
        name='Profile',
        line=dict(color='black', width=2.5)
    ))

    # Background line
    fig_profile.add_hline(y=background, line_dash="dash", line_color="gray", name="Background")

    # AUC areas with draggable boundaries
    def trim_top_25(start, end):
        band_height = end - start
        trim = int(band_height * 0.25)
        return start + trim

    for band in bands:
        left = band['left']
        right = band['right']
        category = band['category']
        color = COLORS[category]

        left_trim = trim_top_25(left, right)

        # AUC area
        band_x = x[left_trim:right+1]
        band_y = profile[left_trim:right+1]

        fig_profile.add_trace(go.Scatter(
            x=band_x, y=band_y,
            fill='tozeroy',
            fillcolor=color,
            opacity=0.35,
            line=dict(color=color, width=2),
            name=category,
            hovertemplate=f'<b>{category}</b><br>%{{x}}<br>%{{y:.3f}}<extra></extra>'
        ))

        # Boundary lines (draggable via shapes)
        fig_profile.add_vline(x=left_trim, line_dash="dash", line_color=color, line_width=2, opacity=0.7)
        fig_profile.add_vline(x=right, line_dash="dash", line_color=color, line_width=2, opacity=0.7)

    fig_profile.update_layout(
        title=f'Tube {tube_idx+1} - Densitometry Profile (Drag boundaries on graph)',
        xaxis_title='Position (pixels)',
        yaxis_title='Optical Density',
        hovermode='x unified',
        template='plotly_white',
        height=500
    )

    # ---- Create Gel Image (Raw ROI) ----
    tube_info = processor.tubes[tube_idx]
    tube_region = tube_info['region']

    # Display raw tube data (no enhancement, just transpose for horizontal view)
    tube_display = np.rot90(tube_region)  # Rotate 90 degrees for horizontal display

    fig_gel = go.Figure()

    # Gel image heatmap
    fig_gel.add_trace(go.Heatmap(
        z=tube_display,
        colorscale='Gray',
        showscale=False,
        hovertemplate='X: %{x}<br>Y: %{y}<br>Intensity: %{z}<extra></extra>',
        name='Tube ROI'
    ))

    fig_gel.update_layout(
        title=f'Tube {tube_idx+1} - ROI (Raw)',
        xaxis_title='Width',
        yaxis_title='Depth',
        template='plotly_white',
        hovermode='closest',
        height=250
    )

    # ---- Results Table ----
    band_aucs, percentages = analyzer.calculate_band_percentages()

    results_data = []
    for band, auc, pct in zip(bands, band_aucs, percentages):
        results_data.append({
            'Lipoprotein': band['category'],
            'AUC': f"{auc:.2f}",
            'Percentage': f"{pct:.1f}%"
        })

    df_results = pd.DataFrame(results_data)

    table = dbc.Table.from_dataframe(
        df_results,
        striped=True,
        bordered=True,
        hover=True,
        className="table-sm"
    )

    # ---- Metrics ----
    metrics = []
    for band, pct in zip(bands, percentages):
        metrics.append(
            dbc.Col([
                dbc.Card([
                    dbc.CardBody([
                        html.H6(band['category'], className="card-title"),
                        html.H4(f"{pct:.1f}%", style={'color': COLORS[band['category']]})
                    ])
                ])
            ], width=3)
        )

    return fig_profile, fig_gel, table, metrics


@callback(
    Output('download-csv', 'data'),
    Input('export-csv-btn', 'n_clicks'),
    [State('tube-selector', 'value'),
     State('processor-store', 'data'),
     State('vldl-slider', 'value'),
     State('idl-slider', 'value'),
     State('ldl-slider', 'value'),
     State('hdl-slider', 'value')],
    prevent_initial_call=True
)
def export_csv(n_clicks, tube_idx, processor_data, vldl, idl, ldl, hdl):
    """Export to CSV"""
    if not processor_data:
        return None

    processor = GelImageProcessor.__new__(GelImageProcessor)
    processor.image_path = processor_data['image_path']
    processor.tubes = []

    for tube_data in processor_data['tubes']:
        region = np.array(tube_data['region'], dtype=np.uint8)
        processor.tubes.append({
            'index': tube_data['index'],
            'region': region,
            'x_range': tuple(tube_data['x_range']),
            'y_range': tuple(tube_data['y_range']),
        })

    profile = processor.get_densitometry_profile(tube_idx, auto_crop=False)
    background = processor.detect_background(profile)
    analyzer = DensitometryAnalyzer(profile, background)
    analyzer.bands = [
        {'left': vldl[0], 'right': vldl[1], 'category': 'VLDL'},
        {'left': idl[0], 'right': idl[1], 'category': 'IDL'},
        {'left': ldl[0], 'right': ldl[1], 'category': 'LDL'},
        {'left': hdl[0], 'right': hdl[1], 'category': 'HDL'},
    ]

    exporter = AnalysisExporter(processor, analyzer, tube_idx)

    import io
    csv_buffer = io.StringIO()
    exporter.export_to_csv('/tmp/analysis.csv')
    with open('/tmp/analysis.csv', 'r') as f:
        csv_content = f.read()

    return dict(content=csv_content, filename=f"tube_{tube_idx+1}_analysis.csv")


@callback(
    Output('download-json', 'data'),
    Input('export-json-btn', 'n_clicks'),
    [State('tube-selector', 'value'),
     State('processor-store', 'data'),
     State('vldl-slider', 'value'),
     State('idl-slider', 'value'),
     State('ldl-slider', 'value'),
     State('hdl-slider', 'value')],
    prevent_initial_call=True
)
def export_json(n_clicks, tube_idx, processor_data, vldl, idl, ldl, hdl):
    """Export to JSON"""
    if not processor_data:
        return None

    processor = GelImageProcessor.__new__(GelImageProcessor)
    processor.image_path = processor_data['image_path']
    processor.tubes = []

    for tube_data in processor_data['tubes']:
        region = np.array(tube_data['region'], dtype=np.uint8)
        processor.tubes.append({
            'index': tube_data['index'],
            'region': region,
            'x_range': tuple(tube_data['x_range']),
            'y_range': tuple(tube_data['y_range']),
        })

    profile = processor.get_densitometry_profile(tube_idx, auto_crop=False)
    background = processor.detect_background(profile)
    analyzer = DensitometryAnalyzer(profile, background)
    analyzer.bands = [
        {'left': vldl[0], 'right': vldl[1], 'category': 'VLDL'},
        {'left': idl[0], 'right': idl[1], 'category': 'IDL'},
        {'left': ldl[0], 'right': ldl[1], 'category': 'LDL'},
        {'left': hdl[0], 'right': hdl[1], 'category': 'HDL'},
    ]

    exporter = AnalysisExporter(processor, analyzer, tube_idx)
    exporter.export_to_json('/tmp/analysis.json')

    with open('/tmp/analysis.json', 'r') as f:
        json_content = f.read()

    return dict(content=json_content, filename=f"tube_{tube_idx+1}_analysis.json")


@callback(
    Output('download-txt', 'data'),
    Input('export-txt-btn', 'n_clicks'),
    [State('tube-selector', 'value'),
     State('processor-store', 'data'),
     State('vldl-slider', 'value'),
     State('idl-slider', 'value'),
     State('ldl-slider', 'value'),
     State('hdl-slider', 'value')],
    prevent_initial_call=True
)
def export_summary(n_clicks, tube_idx, processor_data, vldl, idl, ldl, hdl):
    """Export summary"""
    if not processor_data:
        return None

    processor = GelImageProcessor.__new__(GelImageProcessor)
    processor.image_path = processor_data['image_path']
    processor.tubes = []

    for tube_data in processor_data['tubes']:
        region = np.array(tube_data['region'], dtype=np.uint8)
        processor.tubes.append({
            'index': tube_data['index'],
            'region': region,
            'x_range': tuple(tube_data['x_range']),
            'y_range': tuple(tube_data['y_range']),
        })

    profile = processor.get_densitometry_profile(tube_idx, auto_crop=False)
    background = processor.detect_background(profile)
    analyzer = DensitometryAnalyzer(profile, background)
    analyzer.bands = [
        {'left': vldl[0], 'right': vldl[1], 'category': 'VLDL'},
        {'left': idl[0], 'right': idl[1], 'category': 'IDL'},
        {'left': ldl[0], 'right': ldl[1], 'category': 'LDL'},
        {'left': hdl[0], 'right': hdl[1], 'category': 'HDL'},
    ]

    exporter = AnalysisExporter(processor, analyzer, tube_idx)
    exporter.export_summary('/tmp/summary.txt')

    with open('/tmp/summary.txt', 'r') as f:
        txt_content = f.read()

    return dict(content=txt_content, filename=f"tube_{tube_idx+1}_summary.txt")


# Sync input fields with sliders for all bands
for band_name in ['vldl', 'idl', 'ldl', 'hdl']:
    @callback(
        [Output(f'{band_name}-slider', 'value'),
         Output(f'{band_name}-min-input', 'value'),
         Output(f'{band_name}-max-input', 'value')],
        [Input(f'{band_name}-slider', 'value'),
         Input(f'{band_name}-min-input', 'value'),
         Input(f'{band_name}-max-input', 'value')],
        prevent_initial_call=True
    )
    def sync_band_values(slider_val, min_val, max_val, band=band_name):
        """Sync slider and input values"""
        from dash import ctx
        if not ctx.triggered:
            return slider_val, slider_val[0] if slider_val else 0, slider_val[1] if slider_val else 0

        trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

        if trigger_id == f'{band}-slider':
            return slider_val, slider_val[0], slider_val[1]
        else:
            # Input changed, update slider
            min_v = int(min_val) if min_val is not None else 0
            max_v = int(max_val) if max_val is not None else 313
            return [min_v, max_v], min_v, max_v


if __name__ == '__main__':
    import os
    port = int(os.environ.get('PORT', 8050))
    debug = os.environ.get('ENVIRONMENT') != 'production'
    app.run(debug=debug, host='0.0.0.0', port=port)
