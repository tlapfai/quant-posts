from django.shortcuts import render

from plotly.offline import plot
import plotly.graph_objs as go

import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from django_plotly_dash import DjangoDash
#from dash import dcc, html

import plotly.express as px

import QuantLib as ql

import numpy as np


def index(request):
    
    K = 0.05
    barrier_lo = 1.064
    barrier_hi = 1.176
    rebate = 0.
    barrierType = ql.DoubleBarrier.KnockOut
    cash = 40000
    vol = 0.06307
    corr = -0.385
    vol_fx = 0.0473

    today = ql.Date(17,11,2021)
    maturity = ql.Date(17,11,2022)

    today = ql.Date().todaysDate()
    quantoAdj = corr * vol * vol_fx
    riskFreeTS = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.0040477, ql.Actual365Fixed()))
    dividendTS = ql.YieldTermStructureHandle(ql.FlatForward(today, -0.0061277 + quantoAdj, ql.Actual365Fixed()))
    quantoTS = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.023150, ql.Actual365Fixed()))

    loading_style = {'position': 'absolute', 'align-self': 'center', 'width' : '100%' }
    
    app = DjangoDash('gamma_curve')
    app.layout = html.Div([ html.H4(children='Valuation', style={'textAlign':'center'}), 
                            dcc.Loading(id='loading', fullscreen=True, parent_style=loading_style), 
                            dcc.Graph(id="gamma-graph"), 
                            html.Table([
                                html.Label('Measure'), 
                                dcc.RadioItems(id='measure', value='NPV', 
                                            options=[{'label':'NPV', 'value':'NPV'}, 
                                                    {'label':'Delta', 'value':'Delta'}, 
                                                    {'label':'Gamma', 'value':'Gamma'},
                                                    {'label':'Vega', 'value':'Vega'}]), 
                                ], 
                                style = {"border" : "1px solid skyblue", "width" : "100%" }
                                ), 
                            html.Table([
                                html.Label('Volatility'), 
                                dcc.Slider(id='vol-slider', min=0.01, max=0.08, value=vol, marks={str(x): str(round(100*x,0)) for x in np.arange(0.01,0.08,0.01)}, step=0.01), 
                                ], 
                                style = {"border" : "1px solid skyblue", "width" : "100%" }
                                ),
                            html.Table([
                                html.Label('Strike'), 
                                dcc.Input(id='k-slider', type='number', value=1.12, min=1.00, max=1.2, step=0.01), 
                                ], 
                                style = {"border" : "1px solid skyblue", "width" : "100%" }
                                ),
                            ],
                        className = "gamma_plot", 
                        style = { "width" : "auto" }
            )
    
    
    @app.callback([Output('gamma-graph', 'figure'), Output('loading', 'parent_style')], Input('measure', 'value'), Input('vol-slider', 'value'), Input('k-slider', 'value'))
    def update_figure(measure, selected_vol, selected_k):
        new_loading_style = loading_style
        x_data = np.linspace(1.08, 1.15, 21)
        
        spot = 1.12
        spot_quote = ql.SimpleQuote(spot)
        #vol_data = np.linspace(selected_vol-0.02, selected_vol+0.04, 121)
        plot_vol = ql.SimpleQuote(selected_vol)
        plot_vol_hdl = ql.QuoteHandle(plot_vol)
        volatility = ql.BlackVolTermStructureHandle(ql.BlackConstantVol(today, ql.NullCalendar(), plot_vol_hdl, ql.Actual365Fixed()))
        initialValue = ql.QuoteHandle(spot_quote)
        process = ql.BlackScholesMertonProcess(initialValue, dividendTS, riskFreeTS, volatility)
        engine = ql.AnalyticDoubleBarrierBinaryEngine(process)

        payoff = ql.CashOrNothingPayoff(ql.Option.Call, selected_k, cash)
        euExercise = ql.EuropeanExercise(maturity)

        opt = ql.DoubleBarrierOption(barrierType, barrier_lo, barrier_hi, rebate, payoff, euExercise)
        opt.setPricingEngine(engine)
        
        if measure == 'NPV':
            fun = opt.NPV
        elif measure == 'Delta':
            fun = opt.delta
        elif measure == 'Gamma':
            fun = opt.gamma
            #fun = opt.gamma
        elif measure == 'Vega':
            fun1 = opt.vega
            #fun2 = opt2.vega
        
        y_data = []
        for x in x_data:
        #for v in vol_data:
            spot_quote.setValue(x)
            #plot_vol.setValue(v)
            y_data.append(fun())

        fig = px.line(x=x_data, y=y_data, labels={'x': 'Spot', 'y': measure})
        fig.update_layout(transition_duration=500)
        return fig, new_loading_style
    
    #plot_div = plot([data1, data2], output_type='div')
    
    #return render(request, "index.html", context={'plot_div': plot_div})
    return render(request, "myplotly/index.html")
