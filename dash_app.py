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
import tempfile
from pathlib import Path
from datetime import datetime

from image_processor import GelImageProcessor, DensitometryAnalyzer

# Initialize Dash app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
app.title = "CLIPR - Lipoprint Analysis Tool"

# Color scheme
COLORS = {
    'VLDL': '#FFD700',  # Yellow
    'IDL': '#FF8C00',   # Orange
    'LDL': '#FF0000',   # Red
    'HDL': '#4ECDC4'    # Teal
}

def _reconstruct_analysis(processor_data, tube_idx, vldl, idl, ldl, hdl):
    """Reconstruct processor and analyzer from stored data."""
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

    bands = [
        {'left': vldl[0], 'right': vldl[1], 'category': 'VLDL'},
        {'left': idl[0], 'right': idl[1], 'category': 'IDL'},
        {'left': ldl[0], 'right': ldl[1], 'category': 'LDL'},
        {'left': hdl[0], 'right': hdl[1], 'category': 'HDL'},
    ]

    analyzer = DensitometryAnalyzer(profile, background)
    analyzer.bands = bands

    return processor, analyzer, profile, background, bands


# ============================================================================
# APP LAYOUT
# ============================================================================

app.layout = dbc.Container([
    # Header
    dbc.Row([
        dbc.Col([
            html.H1("CLIPR - Lipoprint Analysis Tool",
                   className="mb-2 mt-4 text-center text-primary"),
            html.H5("Hugues Beaufrère, DVM, PhD, DACZM",
                   className="mb-4 text-center text-muted")
        ])
    ]),

    dbc.Row([
        # LEFT COLUMN - Controls
        dbc.Col([
            # Logo
            html.Div(
                html.Img(src='/assets/logo.jpg', style={'max-width': '100%', 'max-height': '120px'}),
                style={'text-align': 'center', 'margin-bottom': '10px'}
            ),
            dbc.Card([
                dbc.CardBody([
                    html.H4("Image Upload", className="card-title"),

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

                    html.Label("VLDL:", className="fw-bold", style={'color': '#FFD700'}),
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

                    html.Label("IDL:", className="fw-bold", style={'color': '#FF8C00'}),
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

                    html.Label("LDL:", className="fw-bold", style={'color': '#FF0000'}),
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

                    html.Label("HDL:", className="fw-bold", style={'color': '#4ECDC4'}),
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
                        style={'height': '200px'}
                    ),

                    html.Hr(),

                    # Patient Information
                    html.Label("Patient Information:", className="fw-bold"),
                    dbc.Row([
                        dbc.Col([
                            dcc.Input(
                                id='pet-name-input',
                                type='text',
                                placeholder='Pet name',
                                className='form-control form-control-sm',
                                style={'font-size': '13px', 'padding': '5px'}
                            )
                        ], width=3),
                        dbc.Col([
                            dcc.Input(
                                id='owner-name-input',
                                type='text',
                                placeholder='Owner name',
                                className='form-control form-control-sm',
                                style={'font-size': '13px', 'padding': '5px'}
                            )
                        ], width=3),
                        dbc.Col([
                            dcc.Input(
                                id='species-input',
                                type='text',
                                placeholder='Species',
                                className='form-control form-control-sm',
                                style={'font-size': '13px', 'padding': '5px'}
                            )
                        ], width=3),
                        dbc.Col([
                            dcc.Input(
                                id='case-number-input',
                                type='text',
                                placeholder='Case #',
                                className='form-control form-control-sm',
                                style={'font-size': '13px', 'padding': '5px'}
                            )
                        ], width=3),
                    ], className="mb-2"),

                    # Cholesterol Input
                    dbc.Row([
                        dbc.Col([
                            html.Label("Total Cholesterol (mg/dL):", className="fw-bold"),
                            dcc.Input(
                                id='cholesterol-input',
                                type='number',
                                placeholder='Enter value',
                                value=None,
                                min=0,
                                className='form-control form-control-sm',
                                style={'font-size': '13px', 'padding': '5px'}
                            )
                        ], width=6),
                    ], className="mb-2"),

                    html.Hr(),

                    # Results Table
                    html.Label("Lipoprotein Profile:", className="fw-bold"),
                    html.Div(id='results-table'),

                    html.Br(),

                    # Metrics
                    dbc.Row(id='metrics-row'),

                    html.Hr(),

                    # Export Buttons
                    html.Label("Export:", className="fw-bold"),
                    dbc.Row([
                        dbc.Col([
                            html.Label("Tube for PDF:", className="small"),
                            dcc.Dropdown(
                                id='pdf-tube-selector',
                                options=[{'label': f'Tube {i+1}', 'value': i} for i in range(12)],
                                value=0,
                                clearable=False,
                                style={'font-size': '12px'}
                            ),
                        ], width=3),
                        dbc.Col([
                            dcc.Download(id='download-pdf'),
                            dbc.Button("PDF Report", id='export-pdf-btn', color="primary", size="sm", className="w-100 mt-4")
                        ], width=3),
                        dbc.Col([
                            dbc.Button("Copy Table", id='copy-table-btn', color="success", size="sm", className="w-100 mt-4"),
                            html.Div(id='copy-feedback', style={'font-size': '11px', 'margin-top': '2px'})
                        ], width=3),
                    ]),

                ])
            ])
        ], width=9),
    ]),

    # SUMMARY TABLE SECTION
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H4("All Tubes Summary", className="card-title"),
                    html.Div(id='summary-table', children=[
                        html.P("Analyze tubes to populate the summary.", className="text-muted")
                    ])
                ])
            ])
        ])
    ], className="mt-4"),

    # Hidden stores for state management
    dcc.Store(id='processor-store', storage_type='memory'),
    dcc.Store(id='analyzer-store', storage_type='memory'),
    dcc.Store(id='table-tsv-store', storage_type='memory'),
    dcc.Store(id='all-tubes-store', data={}, storage_type='memory'),
    dcc.Store(id='patient-info-store', data={}, storage_type='memory'),

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
     Output('hdl-slider', 'disabled'),
     Output('vldl-min-input', 'disabled'),
     Output('vldl-max-input', 'disabled'),
     Output('idl-min-input', 'disabled'),
     Output('idl-max-input', 'disabled'),
     Output('ldl-min-input', 'disabled'),
     Output('ldl-max-input', 'disabled'),
     Output('hdl-min-input', 'disabled'),
     Output('hdl-max-input', 'disabled')],
    Input('processor-store', 'data')
)
def enable_controls(processor_data):
    """Enable controls when image is loaded"""
    enabled = processor_data is not None
    return [not enabled] * 13


@callback(
    Output('reference-tubes', 'children'),
    [Input('processor-store', 'data'),
     Input('tube-selector', 'value')]
)
def display_reference_tubes(processor_data, selected_tube):
    """Display all 12 tubes as reference grid with selected tube highlighted"""
    if not processor_data:
        return html.Div("Load image to see reference", className="text-muted small")

    try:
        from PIL import Image
        tubes_data = processor_data['tubes']
        if not tubes_data:
            return html.Div("No tubes found", className="text-muted small")

        if selected_tube is None:
            selected_tube = 0

        tube_elements = []
        for i, tube_data in enumerate(tubes_data):
            region = np.array(tube_data['region'], dtype=np.uint8)
            rotated = np.rot90(region)

            img_pil = Image.fromarray(rotated.astype(np.uint8))
            buf = io.BytesIO()
            img_pil.save(buf, format='PNG')
            buf.seek(0)
            img_b64 = base64.b64encode(buf.getvalue()).decode()

            is_selected = (i == selected_tube)
            border_style = '3px solid #0d6efd' if is_selected else '1px solid #ddd'
            bg_color = '#e7f1ff' if is_selected else 'transparent'

            tube_elements.append(
                html.Div([
                    html.Div(
                        f"T{i+1}",
                        style={
                            'font-size': '10px',
                            'font-weight': 'bold' if is_selected else 'normal',
                            'color': '#0d6efd' if is_selected else '#666',
                            'width': '24px',
                            'text-align': 'right',
                            'margin-right': '4px',
                            'flex-shrink': '0',
                        }
                    ),
                    html.Img(
                        src=f'data:image/png;base64,{img_b64}',
                        style={
                            'width': '100%',
                            'border': border_style,
                            'border-radius': '2px',
                        }
                    ),
                ], style={
                    'display': 'flex',
                    'align-items': 'center',
                    'margin-bottom': '2px',
                    'padding': '2px',
                    'background-color': bg_color,
                    'border-radius': '4px',
                })
            )

        return html.Div(tube_elements)
    except Exception as e:
        return html.Div(f"Error: {str(e)}", className="text-danger small")


# --- Patient info save/load ---

@callback(
    Output('patient-info-store', 'data'),
    [Input('pet-name-input', 'value'),
     Input('owner-name-input', 'value'),
     Input('species-input', 'value'),
     Input('case-number-input', 'value'),
     Input('cholesterol-input', 'value')],
    [State('tube-selector', 'value'),
     State('patient-info-store', 'data')],
    prevent_initial_call=True
)
def save_patient_info(pet_name, owner_name, species, case_number, cholesterol,
                      tube_idx, store):
    """Save patient info fields to store for the current tube"""
    if store is None:
        store = {}
    key = str(tube_idx) if tube_idx is not None else '0'
    store[key] = {
        'pet_name': pet_name or '',
        'owner_name': owner_name or '',
        'species': species or '',
        'case_number': case_number or '',
        'cholesterol': cholesterol,
    }
    return store


@callback(
    [Output('pet-name-input', 'value'),
     Output('owner-name-input', 'value'),
     Output('species-input', 'value'),
     Output('case-number-input', 'value'),
     Output('cholesterol-input', 'value')],
    Input('tube-selector', 'value'),
    State('patient-info-store', 'data'),
    prevent_initial_call=True
)
def load_tube_info(tube_idx, store):
    """Load patient info for the selected tube, or clear if not yet set"""
    if store and str(tube_idx) in store:
        info = store[str(tube_idx)]
        return (
            info.get('pet_name', ''),
            info.get('owner_name', ''),
            info.get('species', ''),
            info.get('case_number', ''),
            info.get('cholesterol'),
        )
    return '', '', '', '', None


# --- Main analysis ---

@callback(
    [Output('profile-graph', 'figure'),
     Output('gel-graph', 'figure'),
     Output('results-table', 'children'),
     Output('metrics-row', 'children'),
     Output('table-tsv-store', 'data'),
     Output('all-tubes-store', 'data')],
    [Input('tube-selector', 'value'),
     Input('vldl-slider', 'value'),
     Input('idl-slider', 'value'),
     Input('ldl-slider', 'value'),
     Input('hdl-slider', 'value'),
     Input('processor-store', 'data'),
     Input('cholesterol-input', 'value')],
    [State('all-tubes-store', 'data')],
    prevent_initial_call=True
)
def update_analysis(tube_idx, vldl, idl, ldl, hdl, processor_data, cholesterol_value,
                    tubes_store):
    """Update all visualizations and results, save to all-tubes store"""

    if not processor_data:
        return {}, {}, "Load an image to start", [], None, tubes_store or {}

    if tubes_store is None:
        tubes_store = {}

    processor, analyzer, profile, background, bands = _reconstruct_analysis(
        processor_data, tube_idx, vldl, idl, ldl, hdl
    )

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

        # Boundary lines
        fig_profile.add_vline(x=left_trim, line_dash="dash", line_color=color, line_width=2, opacity=0.7)
        fig_profile.add_vline(x=right, line_dash="dash", line_color=color, line_width=2, opacity=0.7)

    fig_profile.update_layout(
        title=f'Tube {tube_idx+1} - Densitometry Profile',
        xaxis_title='Position (pixels)',
        yaxis_title='Optical Density',
        hovermode='x unified',
        template='plotly_white',
        height=500
    )

    # ---- Create Gel Image (Raw ROI) ----
    tube_info = processor.tubes[tube_idx]
    tube_region = tube_info['region']
    tube_display = np.rot90(tube_region)

    fig_gel = go.Figure()
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
        height=180,
        margin=dict(l=40, r=20, t=30, b=30)
    )

    # ---- Results Table ----
    band_aucs, percentages = analyzer.calculate_band_percentages()

    # Calculate Total LDL (IDL + LDL)
    idl_idx = next(i for i, b in enumerate(bands) if b['category'] == 'IDL')
    ldl_idx = next(i for i, b in enumerate(bands) if b['category'] == 'LDL')
    total_ldl_auc = band_aucs[idl_idx] + band_aucs[ldl_idx]
    total_ldl_pct = percentages[idl_idx] + percentages[ldl_idx]

    results_data = []
    for band, auc, pct in zip(bands, band_aucs, percentages):
        row = {
            'Lipoprotein': band['category'],
            'AUC': f"{auc:.2f}",
            'Percentage': f"{pct:.1f}%"
        }
        if cholesterol_value and cholesterol_value > 0:
            cholesterol_mg = (pct / 100.0) * cholesterol_value
            row['Cholesterol (mg/dL)'] = f"{cholesterol_mg:.1f}"
        results_data.append(row)

        if band['category'] == 'LDL':
            total_row = {
                'Lipoprotein': 'Total LDL (IDL+LDL)',
                'AUC': f"{total_ldl_auc:.2f}",
                'Percentage': f"{total_ldl_pct:.1f}%"
            }
            if cholesterol_value and cholesterol_value > 0:
                total_row['Cholesterol (mg/dL)'] = f"{(total_ldl_pct / 100.0) * cholesterol_value:.1f}"
            results_data.append(total_row)

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

    # ---- TSV data for clipboard ----
    has_chol = cholesterol_value and cholesterol_value > 0
    if has_chol:
        tsv_data = "Lipoprotein\tAUC\tPercentage (%)\tCholesterol (mg/dL)\n"
        for band, auc, pct in zip(bands, band_aucs, percentages):
            chol = (pct / 100.0) * cholesterol_value
            tsv_data += f"{band['category']}\t{auc:.2f}\t{pct:.1f}\t{chol:.1f}\n"
            if band['category'] == 'LDL':
                total_chol = (total_ldl_pct / 100.0) * cholesterol_value
                tsv_data += f"Total LDL (IDL+LDL)\t{total_ldl_auc:.2f}\t{total_ldl_pct:.1f}\t{total_chol:.1f}\n"
        tsv_data += f"\nTotal Cholesterol\t\t\t{cholesterol_value}"
    else:
        tsv_data = "Lipoprotein\tAUC\tPercentage (%)\n"
        for band, auc, pct in zip(bands, band_aucs, percentages):
            tsv_data += f"{band['category']}\t{auc:.2f}\t{pct:.1f}\n"
            if band['category'] == 'LDL':
                tsv_data += f"Total LDL (IDL+LDL)\t{total_ldl_auc:.2f}\t{total_ldl_pct:.1f}\n"

    # ---- Save to all-tubes store ----
    tubes_store[str(tube_idx)] = {
        'vldl_pct': float(percentages[0]),
        'idl_pct': float(percentages[1]),
        'ldl_pct': float(percentages[2]),
        'hdl_pct': float(percentages[3]),
        'total_ldl_pct': float(total_ldl_pct),
        'vldl_auc': float(band_aucs[0]),
        'idl_auc': float(band_aucs[1]),
        'ldl_auc': float(band_aucs[2]),
        'hdl_auc': float(band_aucs[3]),
        'total_ldl_auc': float(total_ldl_auc),
        'vldl': list(vldl),
        'idl': list(idl),
        'ldl': list(ldl),
        'hdl': list(hdl),
    }

    return fig_profile, fig_gel, table, metrics, tsv_data, tubes_store


# --- Summary table ---

@callback(
    Output('summary-table', 'children'),
    [Input('all-tubes-store', 'data'),
     Input('patient-info-store', 'data')]
)
def update_summary_table(tubes_store, patient_store):
    """Build summary table from all analyzed tubes"""
    if not tubes_store:
        return html.P("Analyze tubes to populate the summary.", className="text-muted")

    if patient_store is None:
        patient_store = {}

    rows = []
    for idx in range(12):
        key = str(idx)
        if key not in tubes_store:
            continue
        t = tubes_store[key]
        p = patient_store.get(key, {})
        chol = p.get('cholesterol')
        has_chol = chol and chol > 0

        row = {
            'Tube': idx + 1,
            'Pet Name': p.get('pet_name', ''),
            'Owner': p.get('owner_name', ''),
            'Species': p.get('species', ''),
            'Case #': p.get('case_number', ''),
            'Chol (mg/dL)': f"{chol}" if has_chol else '',
            'VLDL %': f"{t['vldl_pct']:.1f}",
            'IDL %': f"{t['idl_pct']:.1f}",
            'LDL %': f"{t['ldl_pct']:.1f}",
            'Total LDL %': f"{t['total_ldl_pct']:.1f}",
            'HDL %': f"{t['hdl_pct']:.1f}",
        }
        rows.append(row)

    if not rows:
        return html.P("Analyze tubes to populate the summary.", className="text-muted")

    df = pd.DataFrame(rows)
    return dbc.Table.from_dataframe(
        df,
        striped=True,
        bordered=True,
        hover=True,
        className="table-sm",
        style={'font-size': '12px'}
    )


# --- PDF export ---

@callback(
    Output('download-pdf', 'data'),
    Input('export-pdf-btn', 'n_clicks'),
    [State('pdf-tube-selector', 'value'),
     State('processor-store', 'data'),
     State('all-tubes-store', 'data'),
     State('patient-info-store', 'data'),
     State('vldl-slider', 'value'),
     State('idl-slider', 'value'),
     State('ldl-slider', 'value'),
     State('hdl-slider', 'value'),
     State('tube-selector', 'value')],
    prevent_initial_call=True
)
def export_pdf(n_clicks, pdf_tube_idx, processor_data, tubes_store, patient_store,
               vldl, idl, ldl, hdl, current_tube_idx):
    """Export PDF report for the selected tube"""
    if not processor_data:
        return None

    try:
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        from fpdf import FPDF
        from PIL import Image
        import os

        # Determine band limits: use stored if available, else current sliders
        key = str(pdf_tube_idx)
        if tubes_store and key in tubes_store:
            t = tubes_store[key]
            use_vldl = t['vldl']
            use_idl = t['idl']
            use_ldl = t['ldl']
            use_hdl = t['hdl']
        else:
            use_vldl = vldl
            use_idl = idl
            use_ldl = ldl
            use_hdl = hdl

        # Get patient info
        p = (patient_store or {}).get(key, {})
        pet_name = p.get('pet_name', '')
        owner_name = p.get('owner_name', '')
        species = p.get('species', '')
        case_number = p.get('case_number', '')
        cholesterol_value = p.get('cholesterol')

        processor, analyzer, profile, background, bands = _reconstruct_analysis(
            processor_data, pdf_tube_idx, use_vldl, use_idl, use_ldl, use_hdl
        )
        band_aucs, percentages = analyzer.calculate_band_percentages()

        # Calculate Total LDL (IDL + LDL)
        idl_idx = next(i for i, b in enumerate(bands) if b['category'] == 'IDL')
        ldl_idx = next(i for i, b in enumerate(bands) if b['category'] == 'LDL')
        total_ldl_auc = band_aucs[idl_idx] + band_aucs[ldl_idx]
        total_ldl_pct = percentages[idl_idx] + percentages[ldl_idx]

        def trim_top_25(start, end):
            return start + int((end - start) * 0.25)

        # --- Densitometry profile chart via matplotlib ---
        x = np.arange(len(profile))
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.plot(x, profile, color='black', linewidth=1.5, label='Profile')
        ax.axhline(y=background, color='gray', linestyle='--', linewidth=1, label='Background')

        for band in bands:
            left = band['left']
            right = band['right']
            cat = band['category']
            color = COLORS[cat]
            lt = trim_top_25(left, right)
            band_x = x[lt:right+1]
            band_y = profile[lt:right+1]
            ax.fill_between(band_x, 0, band_y, color=color, alpha=0.35, label=cat)
            ax.axvline(x=lt, color=color, linestyle='--', linewidth=1, alpha=0.7)
            ax.axvline(x=right, color=color, linestyle='--', linewidth=1, alpha=0.7)

        ax.set_title(f'Tube {pdf_tube_idx+1} - Densitometry Profile')
        ax.set_xlabel('Position (pixels)')
        ax.set_ylabel('Optical Density')
        ax.legend(loc='upper left', fontsize=8, framealpha=0.9)
        ax.set_xlim(0, len(profile))
        fig.tight_layout()

        profile_tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        fig.savefig(profile_tmp.name, dpi=150, bbox_inches='tight')
        plt.close(fig)

        # --- Tube ROI image via PIL ---
        tube_region = processor.tubes[pdf_tube_idx]['region']
        tube_display = np.rot90(tube_region)
        img_pil = Image.fromarray(tube_display.astype(np.uint8))
        gel_tmp = tempfile.NamedTemporaryFile(suffix='.png', delete=False)
        img_pil.save(gel_tmp.name, format='PNG')
        gel_tmp.close()

        # --- Create PDF ---
        pdf = FPDF()
        pdf.add_page()

        # Logo
        logo_path = Path(__file__).parent / 'assets' / 'logo.jpg'
        if logo_path.exists():
            pdf.image(str(logo_path), x=80, w=50)
            pdf.ln(3)

        # Title
        pdf.set_font('Helvetica', 'B', 18)
        pdf.cell(0, 10, 'CLIPR - Lipoprint Analysis Tool', ln=True, align='C')
        pdf.set_font('Helvetica', '', 11)
        pdf.cell(0, 7, 'Hugues Beaufrere, DVM, PhD, DACZM', ln=True, align='C')
        pdf.ln(3)
        pdf.set_font('Helvetica', '', 9)
        pdf.cell(0, 5, f'Date: {datetime.now().strftime("%Y-%m-%d %H:%M")}    |    Tube: {pdf_tube_idx + 1}', ln=True, align='C')
        pdf.ln(4)

        # Patient information
        pdf.set_font('Helvetica', '', 10)
        info_w = 95
        if pet_name:
            pdf.cell(info_w, 6, f'Pet Name: {pet_name}', 0, 0)
        else:
            pdf.cell(info_w, 6, '', 0, 0)
        if owner_name:
            pdf.cell(info_w, 6, f'Owner: {owner_name}', 0, 1)
        else:
            pdf.cell(info_w, 6, '', 0, 1)
        if species:
            pdf.cell(info_w, 6, f'Species: {species}', 0, 0)
        else:
            pdf.cell(info_w, 6, '', 0, 0)
        if case_number:
            pdf.cell(info_w, 6, f'Case #: {case_number}', 0, 1)
        else:
            pdf.cell(info_w, 6, '', 0, 1)
        pdf.ln(3)

        # Densitometry graph
        pdf.image(profile_tmp.name, x=10, w=190)
        pdf.ln(3)

        # Tube image
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, f'Tube {pdf_tube_idx+1} - ROI', ln=True)
        pdf.image(gel_tmp.name, x=10, w=190)
        pdf.ln(5)

        # Results table
        pdf.set_font('Helvetica', 'B', 12)
        pdf.cell(0, 8, 'Lipoprotein Profile', ln=True)
        pdf.ln(2)

        has_chol = cholesterol_value and cholesterol_value > 0

        # Table header
        pdf.set_font('Helvetica', 'B', 10)
        pdf.set_fill_color(230, 230, 230)
        col_w = 45 if not has_chol else 38
        pdf.cell(col_w, 8, 'Lipoprotein', 1, 0, 'C', True)
        pdf.cell(col_w, 8, 'AUC', 1, 0, 'C', True)
        pdf.cell(col_w, 8, 'Percentage', 1, 0, 'C', True)
        if has_chol:
            pdf.cell(col_w, 8, 'Chol (mg/dL)', 1, 0, 'C', True)
        pdf.ln()

        # Table rows
        pdf.set_font('Helvetica', '', 10)
        for band, auc, pct in zip(bands, band_aucs, percentages):
            pdf.cell(col_w, 7, band['category'], 1, 0, 'C')
            pdf.cell(col_w, 7, f'{auc:.2f}', 1, 0, 'C')
            pdf.cell(col_w, 7, f'{pct:.1f}%', 1, 0, 'C')
            if has_chol:
                chol = (pct / 100.0) * cholesterol_value
                pdf.cell(col_w, 7, f'{chol:.1f}', 1, 0, 'C')
            pdf.ln()

            # Total LDL row after LDL
            if band['category'] == 'LDL':
                pdf.set_font('Helvetica', 'B', 10)
                pdf.cell(col_w, 7, 'Total LDL (IDL+LDL)', 1, 0, 'C')
                pdf.cell(col_w, 7, f'{total_ldl_auc:.2f}', 1, 0, 'C')
                pdf.cell(col_w, 7, f'{total_ldl_pct:.1f}%', 1, 0, 'C')
                if has_chol:
                    total_chol = (total_ldl_pct / 100.0) * cholesterol_value
                    pdf.cell(col_w, 7, f'{total_chol:.1f}', 1, 0, 'C')
                pdf.ln()
                pdf.set_font('Helvetica', '', 10)

        if has_chol:
            pdf.ln(3)
            pdf.set_font('Helvetica', 'B', 10)
            pdf.cell(0, 7, f'Total Cholesterol: {cholesterol_value} mg/dL', ln=True)

        # Output PDF
        pdf_bytes = pdf.output()

        # Cleanup temp files
        os.unlink(profile_tmp.name)
        os.unlink(gel_tmp.name)

        pdf_b64 = base64.b64encode(pdf_bytes).decode()
        return dict(content=pdf_b64, filename=f'tube_{pdf_tube_idx+1}_report.pdf', base64=True)

    except Exception as e:
        print(f"PDF export error: {e}")
        import traceback
        traceback.print_exc()
        return None


# Sync PDF tube selector with main tube selector
@callback(
    Output('pdf-tube-selector', 'value'),
    Input('tube-selector', 'value'),
    prevent_initial_call=True
)
def sync_pdf_tube(tube_idx):
    return tube_idx


# Clientside callback for clipboard copy
app.clientside_callback(
    """
    function(n_clicks, tsvData) {
        if (!n_clicks || !tsvData) {
            return '';
        }
        navigator.clipboard.writeText(tsvData).then(function() {
            // success
        }).catch(function(err) {
            console.error('Copy failed:', err);
        });
        return '\u2713 Copied!';
    }
    """,
    Output('copy-feedback', 'children'),
    Input('copy-table-btn', 'n_clicks'),
    State('table-tsv-store', 'data'),
    prevent_initial_call=True
)


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
