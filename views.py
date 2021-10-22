from django.shortcuts import render

from plotly.offline import plot
import plotly.graph_objs as go
import plotly.express as px
import QuantLib as ql



def index(request):

    strike = 100.0
    maturity = ql.Date(15,12,2021)
    option_type = ql.Option.Call

    payoff = ql.PlainVanillaPayoff(option_type, strike)
    #binaryPayoff = ql.CashOrNothingPayoff(option_type, strike, 1)

    europeanExercise = ql.EuropeanExercise(maturity)
    europeanOption = ql.VanillaOption(payoff, europeanExercise)

    today = ql.Date().todaysDate()
    riskFreeTS = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.05, ql.Actual365Fixed()))
    dividendTS = ql.YieldTermStructureHandle(ql.FlatForward(today, 0.01, ql.Actual365Fixed()))
    volatility = ql.BlackVolTermStructureHandle(ql.BlackConstantVol(today, ql.NullCalendar(), 0.1, ql.Actual365Fixed()))
    a = ql.SimpleQuote(110)
    initialValue = ql.QuoteHandle(a)
    process = ql.BlackScholesMertonProcess(initialValue, dividendTS, riskFreeTS, volatility)

    engine = ql.AnalyticEuropeanEngine(process)
    europeanOption.setPricingEngine(engine)
    
    x_data = list(range(80, 120+1))
    y_data = []
    for x in x_data:
        a.setValue(x)
        y = float(europeanOption.gamma())
        y_data.append(y)
        
    plot_div = plot([go.Scatter(x=x_data, y=y_data,
                        mode='lines', name='test',
                        opacity=0.8, marker_color='green')],
               output_type='div')
    return render(request, "index.html", context={'plot_div': plot_div})
