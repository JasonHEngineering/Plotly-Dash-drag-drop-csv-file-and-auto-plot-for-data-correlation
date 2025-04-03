# -*- coding: utf-8 -*-
"""
V2 - update to avoid app trigger on first web loading
V2 - corrected wrong colours on correlation chart
V2 - update data=df.to_dict('rows') to data=df.to_dict(orient='records'), due to deprecation
V2 - update XY scatter chart to have another dropdown options so as to assign colour by another label group

"""

import base64
import io
import plotly.graph_objs as go
import plotly.express as px  # For automatic color selection
import numpy as np
import dash
from dash.dependencies import Input, Output#, State
from dash import dcc
from dash import html
from dash import dash_table
import pandas as pd
import dash_bootstrap_components as dbc
from plotly.subplots import make_subplots

app = dash.Dash(__name__, suppress_callback_exceptions=True, title='Dash Upload')

background_colors = {"graphBackground": "#F5F5F5", "background": "#ffffff", "text": "#000000"}

colors = px.colors.qualitative.Set1  # You can change this to other color sets

app.layout = html.Div([

dcc.Store(id='memory-output'),

html.Div(
    [
     html.H4('Select and/or drop CSV file!')
     ], className='row'),

html.Div(
    [
        dcc.Upload(
            id="upload-data",
            children=html.Div(["Drag and Drop or ", html.A("Select Files")]),
            style={
                "width": "100%",
                "height": "60px",
                "lineHeight": "60px",
                "borderWidth": "1px",
                "borderStyle": "dashed",
                "borderRadius": "5px",
                "textAlign": "center",
                "margin": "10px",
            },
            # Allow multiple files to be uploaded
            multiple=True,
        ),

        dbc.Spinner(dcc.Graph(id="correlation_matrix")),

        dbc.Spinner(dcc.Graph(id="facet_matrix")),

        html.Div([
            dcc.Dropdown(
                id='list_of_df_headers_for_x_axis',
                value=None,
                placeholder="Select X-Axis",
        )],style={"width": "20%"},),

        html.Br(),

        html.Div([
            dcc.Dropdown(
                id='list_of_df_headers_for_y_axis',
                value=None,
                placeholder="Select Y-Axis",
        )],style={"width": "20%"},),

        html.Br(),

        html.Div([
            dcc.Dropdown(
                id='list_of_df_headers_for_colour',
                value=None,
                placeholder="Select colour group",
        )],style={"width": "20%"},),

        html.Br(),

        dcc.Graph(id="XYgraph"),
        html.Div(id="output-data-upload"),
    ], style={'marginTop': 25, 'marginLeft': 50, 'marginRight': 50}),

])


@app.callback(
    Output("correlation_matrix", "figure"),
    [Input("upload-data", "contents"),
     Input("upload-data", "filename")
     ],
    prevent_initial_call=True  # Prevents callback from triggering on initial page load
)
def correlation_graph(contents, filename):

    if contents:
        contents = contents[0]
        filename = filename[0]
        df = parse_data(contents, filename)

    for column in df:
        if df[column].dtypes == "object":
            df[column] = df.groupby(column).ngroup()

    corr = df.corr() # default is pearson correlation method


    col_name = corr.columns
    col_values = corr.values

    col_values = np.round(col_values,2)

    fig1 = go.Figure(data=go.Heatmap(
                        z=corr.iloc[::1],
                        x=col_name,
                        y=col_name[::1],
                        colorscale='RdBu',
                        text=col_values,
                        texttemplate="%{text}",
                        #texttemplate=corr,
                        textfont={"size":16}
                        ))

    return fig1


@app.callback(
    Output("facet_matrix", "figure"),
    [Input("upload-data", "contents"),
     Input("upload-data", "filename")
     ],
    prevent_initial_call=True  # Prevents callback from triggering on initial page load
)
def facet_graph(contents, filename):

    if contents:
        contents = contents[0]
        filename = filename[0]
        df_original = parse_data(contents, filename)


        fig5 = go.Figure(make_subplots(rows=len(df_original.columns),
                      cols=len(df_original.columns),
                      shared_xaxes=True,
                      shared_yaxes=True,
                      column_titles=list(df_original.columns),
                      row_titles=list(df_original.columns),
                      horizontal_spacing=0.01,
                      vertical_spacing=0.03,
                      start_cell="top-left")
                          )

        for i, name_i in enumerate(df_original.columns):
            for j, name_j in enumerate(df_original.columns):

                fig5.add_trace(go.Scatter(x=df_original[name_j], y=df_original[name_i], mode='markers'),
                          row=i+1, col=j+1)

            fig5.layout.annotations[i]["font"] = {'size': 12}
            fig5.layout.annotations[i+len(df_original.columns)]["font"] = {'size': 12}
            fig5.layout.annotations[i]["text"] = "<b>" + fig5.layout.annotations[i]['text'] + "</b>"
            fig5.layout.annotations[i+len(df_original.columns)]["text"] = "<b>" + fig5.layout.annotations[i+len(df_original.columns)]['text'] + "</b>"

        fig5.update_layout(showlegend=False,
                           height=1200
                            )

    return fig5


@app.callback(
    Output("XYgraph", "figure"),
    Output("memory-output", "data"),
    [Input("upload-data", "contents"),
     Input("upload-data", "filename"),
     Input("list_of_df_headers_for_x_axis", "value"),
     Input("list_of_df_headers_for_y_axis", "value"),
     Input("list_of_df_headers_for_colour", "value"),
     ],
    prevent_initial_call=True  # Prevents callback from triggering on initial page load
)
def update_XYgraph(contents, filename, x_axis_parameter, y_axis_parameter, colour_parameter):

    x = []
    y = []

    if contents:
        contents = contents[0]
        filename = filename[0]
        df = parse_data(contents, filename)
        df_columns = list(df.columns)


        if x_axis_parameter == None:
            x_axis_parameter = df_columns[0]
        x=df[x_axis_parameter]

        if y_axis_parameter == None:
            y_axis_parameter = df_columns[1]
        y=df[y_axis_parameter]


        if colour_parameter == None:
            colour_parameter = df_columns[1]
        unique_categories = df[colour_parameter].unique()

        color_map = {cat: colors[i % len(colors)] for i, cat in enumerate(unique_categories)}

        fig = go.Figure()

        # Add a single trace but with a list of colors from color_map
        fig.add_trace(go.Scatter(
            x=x,
            y=y,
            mode="markers",
            marker=dict(color=[color_map[c] for c in df[colour_parameter]], size=10),
            name="All Points",  # Legend will not be per category here
            showlegend=False  # Hide default legend for a single trace
        ))

        # Manually add legend items with correct colors
        for cat in unique_categories:
            fig.add_trace(go.Scatter(
                x=[None],  # Dummy point for legend
                y=[None],
                mode="markers",
                marker=dict(color=color_map[cat], size=10),
                name=str(cat)  # Legend label
            ))

        # Define layout with legend settings
        layout = go.Layout(

            plot_bgcolor=background_colors["graphBackground"],
            paper_bgcolor=background_colors["graphBackground"],

            xaxis=dict(
                title = x_axis_parameter
            ),
            yaxis=dict(
                title= y_axis_parameter
            ),

            legend=dict(
                #title="Category",
                x=1.05,  # Moves legend outside the plot
                y=1,
                xanchor="left",  # Keeps alignment correct
                yanchor="top",
                bgcolor="rgba(255,255,255,0.5)",  # Semi-transparent background
                bordercolor="black",
                borderwidth=1
            ),
            margin=dict(r=150),  # Add space on the right for the legend
            template="plotly_white"
        )

        fig.update_layout(layout)

        return fig, df_columns

    else:
        pass  # equivalent to return None, None


@app.callback(
    Output("list_of_df_headers_for_x_axis", "options"),
    [Input('memory-output', 'data')],
    prevent_initial_call=True  # Prevents callback from triggering on initial page load
)
def update_x_axis_dropdown(data):

    return [{'label': i, 'value': i} for i in data]

@app.callback(
    Output("list_of_df_headers_for_y_axis", "options"),
    [Input('memory-output', 'data')],
    prevent_initial_call=True  # Prevents callback from triggering on initial page load
)
def update_y_axis_dropdown(data):
    return [{'label': i, 'value': i} for i in data]


@app.callback(
    Output("list_of_df_headers_for_colour", "options"),
    [Input('memory-output', 'data')],
    prevent_initial_call=True  # Prevents callback from triggering on initial page load
)
def update_colour_dropdown(data):
    return [{'label': i, 'value': i} for i in data]


def parse_data(contents, filename):
    content_type, content_string = contents.split(",")

    decoded = base64.b64decode(content_string)
    try:
        if "csv" in filename:
            # Assume that the user uploaded a CSV or TXT file
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")))
        elif "xls" in filename:
            # Assume that the user uploaded an excel file
            df = pd.read_excel(io.BytesIO(decoded))
        elif "txt" or "tsv" in filename:
            # Assume that the user upl, delimiter = r'\s+'oaded an excel file
            df = pd.read_csv(io.StringIO(decoded.decode("utf-8")), delimiter=r"\s+")
    except Exception as e:
        print(e)
        return html.Div(["There was an error processing this file."])

    return df


@app.callback(
    Output("output-data-upload", "children"),
    [Input("upload-data", "contents"), Input("upload-data", "filename")],
    prevent_initial_call=True  # Prevents callback from triggering on initial page load
)


# for displaying raw table
def update_table(contents, filename):
    table = html.Div()

    if contents:
        contents = contents[0]
        filename = filename[0]
        df = parse_data(contents, filename)

        table = html.Div(
            [
                html.H5(filename),
                dash_table.DataTable(
                    data=df.to_dict(orient='records'),
                    columns=[{"name": i, "id": i} for i in df.columns],
                ),
                html.Hr(),
                html.Div("Raw Content"),
                html.Pre(
                    contents[0:200] + "...",
                    style={"whiteSpace": "pre-wrap", "wordBreak": "break-all"},
                ),
            ]
        )

    return table


if __name__ == '__main__':
    app.run_server()