# -*- coding: utf-8 -*-
"""
Created on Wed Feb 26 09:59:38 2020

@author: Manuel G.

This script uses bokeh to create an interactive dashboard to explore the data from my working paper:
"Enchanted wanderer or stone guest: On field-original knowledge and the creativity of invention"

"""

# imports
import pandas as pd
import numpy as np
import math
from bokeh.plotting import ColumnDataSource, figure
from bokeh.palettes import d3, Viridis256
from bokeh.io import output_file, show 
from bokeh.models.mappers import LinearColorMapper
from bokeh.models import BasicTicker, ColorBar, Range1d, HoverTool,Whisker
from bokeh.layouts import column, gridplot
from bokeh.models.widgets import Panel, Tabs, Div

###########################################
## Load data
df = pd.read_csv('{}fok.csv')

###########################################
## Pre-processing
df.rename(columns={'nr_newpairs_uspc6':'novelty','enters_nf_uspc3_all_2':'enters_nf','wgt_avg_trans_rate_2':'fok','top_100_and_50':'bt','fail_25':'fail'},inplace=True)
df['log_novelty'] = np.log(df['novelty']+1)
df['log_cit_10'] = np.log(df['cit_10']+1)
df['nber_cat'] = df['nber_cat'].replace(np.NaN, 9999).astype(int)

quants = 20
df['fok_{}'.format(quants)] = df.groupby(['class','pyear'])['fok'].apply(lambda x: pd.qcut(x.rank(method='first'),quants,duplicates='drop',labels=False))
df['novelty_{}'.format(quants)] = df.groupby(['class','pyear'])['novelty'].apply(lambda x: pd.qcut(x.rank(method='first'),quants,duplicates='drop',labels=False))

# Generate various df's to plot
df_20 = df[['fok_20','novelty_20']].copy().drop_duplicates().reset_index(drop=True)
for var in ['bt','fail','log_cit_10']:
    df_20 = df_20.merge(df.groupby(['fok_20','novelty_20'],as_index=False)[var].mean(),on=['fok_20','novelty_20'])
    if var=='bt' or var=='fail':
        df_20[var] = df_20[var]*100

df_year = df.groupby('pyear',as_index=False)[['inventor_id','assignee_id','appln_id']].nunique()
for i in ['log_novelty','fok','bt','fail','log_cit_10']:
    df_i = df.groupby('pyear',as_index=False)[i].agg(['mean','count','std'])
    mean, lower , upper = [], [], []
    for j in df_i.index:
        mean_, count_, std_ = df_i.loc[j]
        mean.append(mean_)
        lower.append(mean_ - 1.96 * std_ / math.sqrt(count_))
        upper.append(mean_ + 1.96 * std_ / math.sqrt(count_))
    df_year[i] = mean
    df_year['{}_low'.format(i)] = lower
    df_year['{}_hi'.format(i)] = upper
    
df_year_nbercat = df.groupby(['pyear','nber_cat'],as_index=False)[['inventor_id','assignee_id','appln_id']].nunique()
for i in ['log_novelty','fok','bt','fail','log_cit_10']:
    df_i = df.groupby(['pyear','nber_cat'],as_index=False)[i].agg(['mean','count','std'])
    mean, lower , upper = [], [], []
    for j in df_i.index:
        mean_, count_, std_ = df_i.loc[j]
        mean.append(mean_)
        lower.append(mean_ - 1.96 * std_ / math.sqrt(count_))
        upper.append(mean_ + 1.96 * std_ / math.sqrt(count_))
    df_year_nbercat[i] = mean
    df_year_nbercat['{}_low'.format(i)] = lower
    df_year_nbercat['{}_hi'.format(i)] = upper

###########################################
# Palettes
palette = d3['Category10'][8]
palette_nbercat = d3['Category10'][7]
    
###########################################
## Dashboad proper
###########################################

### Tab I: Overview

# Figure 1_a: line plot with patent counts
var = ['appln_id','inventor_id','assignee_id']
varnames = ['Patents','Inventors','Assignees']
color = palette[:3]
tools_to_show = 'hover,box_zoom,pan,save,reset,wheel_zoom'

source_counts_class_pyear = ColumnDataSource(df_year)
fig_1_a = figure(title='Evolution', x_axis_label='Year',plot_width=1000, plot_height=300)
plots = []
for i in range(3):
    fig_1_a.line(x='pyear',y=var[i], source=source_counts_class_pyear, legend_label=varnames[i], color=color[i])
    plots.append(fig_1_a.circle(x='pyear',y=var[i], source=source_counts_class_pyear, size=10, fill_color=color[i], line_color='white',alpha=.1,
                              hover_fill_color=color[i], hover_alpha=.5, hover_line_color='white'))
    fig_1_a.add_tools(HoverTool(renderers=[plots[i]], tooltips=[('Year','@pyear'),(varnames[i], '@{}'.format(var[i]))], mode='mouse'))
    #fig.tools[0].renderers.append(circle)
fig_1_a.legend.location='top_left'

# Figures 1_b - 1_f
source_counts_class_pyear = ColumnDataSource(df_year)
var = ['fok','log_novelty','log_cit_10','bt','fail']
varnames = ['Field-original knowledge','New comb. (log)','Fwd cit 10y (log)','Breakthrough rate','Failure rate']
plot_size = [(500,200),(500,200),(round(1000/3),200),(round(1000/3),200),(round(1000/3),200)]
color = palette[3:]
plots = []
for i in range(5):
    plots.append(figure(title=varnames[i], x_axis_label='Year', plot_width=plot_size[i][0], plot_height=plot_size[i][1]))
    plots[i].y_range=Range1d(source_counts_class_pyear.data['{}_low'.format(var[i])].min()*.98, source_counts_class_pyear.data['{}_hi'.format(var[i])].max()*1.02)
    plots[i].line(x='pyear', y=var[i], source=source_counts_class_pyear, color=color[i])
    w = Whisker(source=source_counts_class_pyear, base="pyear", upper="{}_hi".format(var[i]), lower="{}_low".format(var[i]), level="overlay", line_color=color[i])
    w.upper_head.line_color = color[i]
    w.lower_head.line_color = color[i]
    plots[i].add_layout(w)    
    plots[i].add_tools(HoverTool(tooltips=[('Year','@pyear'),(varnames[i], '@{}'.format(var[i]))], mode='vline'))
fig_1_b = plots[0]
fig_1_c = plots[1]
fig_1_d = plots[2]
fig_1_e = plots[3]
fig_1_f = plots[4]
for fig in [fig_1_c, fig_1_d, fig_1_e, fig_1_f]:
    fig.x_range = fig_1_b.x_range
    
### Tab II: overview by NBER tech categories
# fig_3_a - fig_3_c, 
nber_cats_dict = {1: 'Chemical', 2:'Computer &Communications', 3: 'Drugs & Medical', 4:'Eletrical & Electronic', 5:'Mechanical', 6:'Other', 9999:'NA'}
var = ['appln_id','inventor_id','assignee_id']
varnames = ['Patents','Inventors','Assignees']
plot_size = [(round(1000/3),400),(round(1000/3),400),(570,400)]
color = d3['Category10'][7]
plots = []
sources_nbercat = []
nbercats = list(df_year_nbercat.nber_cat.unique())
for i in range(3):
    plots.append(figure(title=varnames[i], x_axis_label='Year', plot_width=plot_size[i][0], plot_height=plot_size[i][1]))
    df_i = df[['pyear']].drop_duplicates().sort_values('pyear').reset_index(drop=True)
    for nbercat in nbercats:
        df_i = df_i.merge(df_year_nbercat[df_year_nbercat['nber_cat']==nbercat][['pyear',var[i]]], on='pyear').rename(columns={'{}'.format(var[i]):'{}_nbercat_{}'.format(var[i],nbercat)})
    sources_nbercat.append(ColumnDataSource(df_i))
    for j,nbercat in enumerate(nbercats):
        plots[i].line(x='pyear', y='{}_nbercat_{}'.format(var[i],nbercat), source=sources_nbercat[i], color=color[j],legend_label='{}'.format(nber_cats_dict[nbercat]), line_width=1.5)
        plots[i].circle(x='pyear', y='{}_nbercat_{}'.format(var[i],nbercat), source=sources_nbercat[i], size=10, fill_color=color[j], line_color='white', alpha=.1,
                        hover_alpha=.5)
        plots[i].add_tools(HoverTool(tooltips=[('Year','@pyear'),
                                               ('Count', '@{}_nbercat_{}'.format(var[i],nbercat))], mode='mouse'))
    #plots[i].legend.location='top_left'
    if i==2:
        plots[i].add_layout(plots[i].legend[0], 'right')
    else:
        plots[i].legend.visible=False
fig_3_a = plots[0]
fig_3_b = plots[1]
fig_3_c = plots[2]
for fig in [fig_3_b, fig_3_c]:
    fig.x_range = fig_3_a.x_range
    
# figs for fok and novelty
var = ['fok','log_novelty','log_cit_10','bt','fail']
varnames = ['Field-original knowledge','New combinations (log)','Fwd cites 10y (log)','Breakthrough rate','Failure rate']
plot_size = [(500,400),(736,400),(round(1000/3),400),(round(1000/3),400),(570,400)]
color = d3['Category10'][7]
plots = []
sources_nbercat = []
nbercats = list(df_year_nbercat.nber_cat.unique())
df_pyear = df[['pyear']].drop_duplicates().sort_values('pyear').reset_index(drop=True)
for i in range(5):
    plots.append(figure(title=varnames[i], x_axis_label='Year', plot_width=plot_size[i][0], plot_height=plot_size[i][1]))
    df_i = df_pyear.copy()
    for nbercat in nbercats:
        df_i = df_i.merge(df_year_nbercat[df_year_nbercat['nber_cat']==nbercat][['pyear',var[i],'{}_low'.format(var[i]),'{}_hi'.format(var[i])]],
                                                                                                                on='pyear').rename(columns={'{}'.format(var[i]):'{}_nbercat_{}'.format(var[i],nbercat),
                                                                                                                                            '{}_low'.format(var[i]): '{}_low_nbercat_{}'.format(var[i],nbercat),
                                                                                                                                            '{}_hi'.format(var[i]): '{}_hi_nbercat_{}'.format(var[i],nbercat)})
    sources_nbercat.append(ColumnDataSource(df_i))
    ymin, ymax = df_year_nbercat['{}_low'.format(var[i])].min(), df_year_nbercat['{}_hi'.format(var[i])].max()
    for j,nbercat in enumerate(nbercats):
        plots[i].y_range=Range1d(ymin*.98, ymax*1.02)
        plots[i].line(x='pyear', y='{}_nbercat_{}'.format(var[i],nbercat), source=sources_nbercat[i],
                      line_width=1.5, line_color=color[j], legend_label='{}'.format(nber_cats_dict[nbercat]), name='y{}'.format(j))
        w = Whisker(source=sources_nbercat[i], base="pyear", upper='{}_hi_nbercat_{}'.format(var[i],nbercat), lower='{}_low_nbercat_{}'.format(var[i],nbercat), level="overlay", line_color=color[j])
        w.upper_head.line_color = color[j]
        w.lower_head.line_color = color[j]
        plots[i].add_layout(w)
        plots[i].add_tools(HoverTool(tooltips=[('Year','@pyear'),
                                               ('Avg', '@{}_nbercat_{}'.format(var[i],nbercat))], mode='mouse'))
    if (i==1) or (i==4):
        plots[i].add_layout(plots[i].legend[0], 'right')
    if (i==0) or (i==2) or (i==3):
        plots[i].legend.visible=False
fig_3_d = plots[0]
fig_3_e = plots[1]
fig_3_f = plots[2]
fig_3_g = plots[3]
fig_3_h = plots[4]
for fig in [fig_3_e, fig_3_f, fig_3_g, fig_3_h]:
    fig.x_range = fig_3_d.x_range
    
### Tab III: fok and novelty
df_20_fok_nov = df.groupby('fok_20',as_index=False)['log_novelty'].agg(['mean','count','std']).rename(columns={'mean':'log_novelty'})
low , high = [], []
for i in df_20_fok_nov.index:
    mean, count, std = df_20_fok_nov.loc[i]
    low.append(mean - 1.96 * std / math.sqrt(count))
    high.append(mean + 1.96 * std / math.sqrt(count))
df_20_fok_nov['lower'] = low
df_20_fok_nov['upper'] = high

# Figure 2_a: Fok y novelty
source_df_20_fok_nov = ColumnDataSource(df_20_fok_nov)
color = palette[0]
fig_2_a = figure(x_axis_label='Quintiles of field-original knowledge', y_axis_label='New combinations (log)',plot_width=1000, plot_height=300)
fig_2_a.line(x='fok_20',y='log_novelty',source=source_df_20_fok_nov, color=color)
plot = fig_2_a.circle(x='fok_20', y='log_novelty', source = source_df_20_fok_nov, size=5, fill_color=color, line_color='white', alpha=.1,
                    hover_fill_color = color, hover_alpha=.5, hover_line_color='white')
w = Whisker(source=source_df_20_fok_nov, base="fok_20", upper="upper", lower="lower", level="overlay", line_color=color)
w.upper_head.line_color = color
w.lower_head.line_color = color
fig_2_a.add_layout(w)
fig_2_a.add_tools(HoverTool(renderers=[plot], tooltips=[('Fok quintile','@fok_20'),('Avg.','@log_novelty')], mode='vline'))
#show(fig_2_a)

# Figure 2_b - : scatter plot de bt
TOOLS = "hover,save,pan,box_zoom,reset,wheel_zoom"
var = ['log_cit_10','bt','fail']
varnames = ['Fwd cites 10y (log)','Breakthrough rate','Failure rate']
colors = Viridis256
mappers = []
for i in var:
    mappers.append(LinearColorMapper(palette=colors, low=df_20[i].min(), high=df_20[i].max()))

source_df_20 = ColumnDataSource(df_20)
scatters = []
plot_size = round(1000/3)
for i in range(3):
    scatters.append(figure(title='{}'.format(varnames[i]),x_axis_label = 'Quintiles of fok',
                          plot_width=plot_size, plot_height=plot_size,tools=TOOLS, toolbar_location='below',
                          tooltips=[('fok:', '@fok_20'),('novelty:', '@novelty_20'), ('Avg. {}'.format(varnames[i]), '@{}'.format(var[i]))]))    
    scatters[i].grid.grid_line_color = None
    scatters[i].axis.axis_line_color = None
    scatters[i].axis.major_tick_line_color = None
    scatters[i].axis.major_label_text_font_size = "7px"
    scatters[i].axis.major_label_standoff = 0
    scatters[i].xaxis.major_label_orientation = math.pi / 3
    
    scatters[i].rect(x="fok_20", y="novelty_20", width=1, height=1,source=source_df_20,fill_color={'field': var[i], 'transform': mappers[i]},line_color=None)    
    color_bar = ColorBar(color_mapper=mappers[i], major_label_text_font_size="7px",ticker=BasicTicker(desired_num_ticks=len(colors)),
                         #formatter=PrintfTickFormatter(format="%d%%"),
                         label_standoff=6, border_line_color=None)
    scatters[i].add_layout(color_bar, 'right')
    if i==0:
        scatters[i].yaxis.axis_label = 'Quantiles of novelty'
fig_2_b = scatters[0]
fig_2_c = scatters[1]
fig_2_d = scatters[2]

for fig in fig_2_c, fig_2_d:
    fig.x_range = fig_2_b.x_range
    fig.y_range = fig_2_b.y_range

textbox_height = 100

# Tab 4: Data sources and main variables

variables_head = Div(text="""<b>Main variables</b>""", height=textbox_height)
variables_body = Div(text="""<p> <b>Field-original knowledge:</b> weighted average distance between each of the three-digit technology classes in an inventor's prior patents and each of the
three-digit technology classes in the focal patent, weighted by the number of prior patents the inventor filed in the class. Here, 'distance' comes from
a Markov matrix wherein the transition probabilities p_tij represent the probability that a patent-filing inventor in year t with experience in class
i files a patent in class j <br>
<b>New combinations (log):</b> number of subclass combination pairs that never occurred in patents before <br>
<b>Breakthrough:</b> equals one if the invention is among the top 1% most-cited relative to patents applied in the same year and technology class, and zero otherwise <br>
<b>Failure:</b> equals 1 if the invention is among the 25% least-cited patents relative to patents applied in the same year and technology classes <br>
<b>Forward citations 10y (log):</b> Number of citations received by the focal patent within 10 years of its application <br> </p>
""", width=800, height=500)

data_head = Div(text="""<b>Data sources</b>""", height=textbox_height)
data_body = Div(text="""<p> The raw data comes from all U.S. utility patents with first priority dates between 1976 and 2000. Patent data was sourced from Patstat 2018-April and 
USPTO Bulk downloads (v2015). Disambiguated inventor names used to build the patent careers of inventors come from Li et al. (2014) and Balsmeier et al. (2015).
For methodological reasons, explained in the paper, observations are limited to patents filed by inventors residing in the US who work at a firm, and who filed at least two patents with
the same firm. Additionally, only inventors whose first patent was filed after 1976 are included.<br>
The final dataset includes 677,049 observations, 379,127 patents with priority application year between 1986 and 2000, filed by 104,483 inventors working for 9,945 assignee firms. </p>
""", width=800, height=500)

# Tab 5: Abstract

abstract_head = Div(text="""<b>Abstract</b>""", height=textbox_height)
abstract_body = Div(text="""<p>Do inventors with uncommon knowledge produce more creative inventions? The answer is `yes', with reserves.
Using data on the careers of 100,000 inventors over 15 years of corporate U.S. patents and an inventor-firm fixed effects panel, I document that
inventors with field-original knowledge---i.e., uncommon among others who work in the same field---produce inventions which are on average more
 novel and more likely to be exceptionally valuable, but more likely to be failures as well. Additionally, estimates from structural equation
 models illustrate that novelty is at the same time an outcome of the search process and a contributor to the creation of economic breakthroughs.
  Caution is due because the rate of failure increases as well, suggesting uncertainty, rather than recombinant fertility or displaced expertise,
  is the driving mechanism. </p>""", width=800, height=300)

# headings and titles

heading = Div(text="""<p style="font-size:20px"><b>Enchanted Wanderer or Stone Guest? On field-original knowledge and the creativity of invention</b></p><br>
              By Manuel Gigena <br>
              This interactive dashboard is an on-line companion to my <a href="https://sites.google.com/view/mgigena/research">working paper</a> with the 
              same name, and is meant to facilitate exploration of its unique dataset.<br><br>""", height=textbox_height)
              
title_I_1 = Div(text="""<b>I.1. Overview of inventive activity</b>""", height=textbox_height)
title_I_2 = Div(text="""<b>I.2. Independent variables / Mediator</b>""", height=textbox_height)
title_I_3 = Div(text="""<b>I.3. Outcome variables: the value of invention</b>""", height=textbox_height)

notes_I_1 = Div(text="""There is a steady increase in the number of patents, inventors and assignees over time. 
                      The number of inventors per assignee also grows, as well as the number of patents filed by each assignee and by each inventor.""",width=200, height=300)
notes_I_2 = Div(text="""Fok drops slightly over time, especially after 1993.
                      Inventions in the second half of the sampled period seem to originate in less field-original knowledge.
                      <br>
                      Novelty drops sensibly over time, from 0.923 in 1986 to 0.52 in 2000 (a 44% decline).""",width=200, height=200)
notes_I_3 = Div(text="""The distribution of invention value over time is not homogeneous. The most valuable inventions were created around 
                    the middle of the sample period (ca. 1992-1998), with highest average value and breakthrough rates, but 
                      the lowest probability of failure.
                      <br>
                      These figures suggest that the risk profile of inventions decreased between 1986 and ca. 1995.""",width=200, height=200)
                      
title_II_1 = Div(text="""<b>II.1. Overview of inventive activity</b>""", height=textbox_height)
title_II_2 = Div(text="""<b>II.2. Independent variables / Mediator</b>""", height=textbox_height)
title_II_3 = Div(text="""<b>II.3. Outcome variables: the value of invention</b>""", height=textbox_height)

notes_II_1 = Div(text="""The growth of patents, inventors and assignees shows strong differences across technology sectors.
                 <br>
                 The largest growth is in 'Computer & Communications'; the smallest, in 'Mechanical'.""",width=180, height=300)
notes_II_2 = Div(text="""Fok is remarkably stable over time, but there are differences in levels across tech sectors.
                 <br>
                 Inventors in 'Drugs & Medical' have the least field-original knowledge (!) (i.e., the most field-specific knowledge, and 
                 less likely to cross-breed across sectors), and their knowledge tends to get even more field-specific over time.
                 <br>
                 'Chemical' has the smallest decrease in novelty over time; 'Drugs & Medical' the largest.
                 <br><br>
                 'Computer & Comm.' is the sector with largest growth in the period, but is also the least novel one.""",width=180, height=300)
notes_II_3 = Div(text="""Changes in value over time are more evident in 'average value' (as measured by forward cites) than in the binary breakthrough/fail dummies.""",width=180, height=300)

title_III_1 = Div(text="""<b>III.1. The relationship between field-original knowledge and recombinant novelty</b>""", height=textbox_height)
title_III_2 = Div(text="""<b>III.2. Fok, novelty and invention value</b>""", height=textbox_height)

notes_III_1 = Div(text="""The figure plots the average number of new combinations of patents at different quintiles of field-original knowledge.
                  Inventors with more field-original knowledge create inventions that are more novel on average (i.e., with more new combinations of technological components).""",width=180, height=300)
notes_III_2 = Div(text="""The heatmaps plot the value measures against quintiles of novelty and field-original knowledge:
                  <br>
                  1) Greater novelty is associated with more citations on average, at all levels of fok.
                  <br>
                  2) Breakthroughs originate disproportionately in inventors with high fok producing with the largest degree of novelty.
                  <br>
                  3) Greater fok is also tied with larger chance of failure (particularly when producing inventions with a low degree of novelty).""",width=180, height=300)

# Create panels

tab_1 = Panel(child = column(title_I_1, row(fig_1_a, notes_I_1),
                             title_I_2, row(gridplot([[fig_1_b, fig_1_c]]),notes_I_2),
                             title_I_3, row(gridplot([[fig_1_d, fig_1_e, fig_1_f]]), notes_I_3)), title = 'I. Overview')
tab_2 = Panel(child = column(title_II_1, row(gridplot([[fig_3_a, fig_3_b, fig_3_c]]), notes_II_1),
                             title_II_2, row(gridplot([[fig_3_d, fig_3_e]]), notes_II_2),
                             title_II_3, row(gridplot([[fig_3_f, fig_3_g, fig_3_h]]), notes_II_3)), title = 'II. Overview by technology sectors')
tab_3 = Panel(child = column(title_III_1, row(fig_2_a, notes_III_1),
                             title_III_2, row(gridplot([[fig_2_b, fig_2_c, fig_2_d]]), notes_III_2)), title = 'III. Field-original knowledge, novelty and the value of invention')
tab_4 = Panel(child = column(data_head, data_body, variables_head, variables_body), title = 'IV. Data sources and main variables')
tab_5 = Panel(child = column(abstract_head, abstract_body), title = 'V. Abstract')
layout = column(heading,Tabs(tabs=[tab_1, tab_2, tab_3, tab_4, tab_5]))

# Output file and show
output_file('{}main.html'.format(path))
show(layout)
