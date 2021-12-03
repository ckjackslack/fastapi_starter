from bokeh.plotting import figure, show

x = [1, 2, 3, 4, 5]
y1 = [4, 5, 5, 7, 2]
y2 = [2, 3, 4, 5, 6]
p = figure(title = 'Legend example')
line = p.line(x, y1, legend_label = 'Temp.',
    line_color = 'blue', line_width = 2)
circle = p.circle(x, y2,
    legend_label = 'Objects', fill_color = 'red',
    fill_alpha = 0.5, line_color = 'blue', size = 80,
)
p.legend.location = 'top_left'
p.legend.title = 'Obervations'
p.legend.label_text_font = 'times'
p.legend.label_text_font_style = 'italic'
p.legend.label_text_color = 'navy'
p.legend.border_line_width = 3
p.legend.border_line_color = 'navy'
p.legend.border_line_alpha = 0.8
p.legend.background_fill_color = 'navy'
p.legend.background_fill_alpha = 0.2

show(p)

# https://docs.bokeh.org/en/latest/docs/first_steps.html