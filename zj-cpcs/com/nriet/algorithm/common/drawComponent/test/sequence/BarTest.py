import matplotlib
import matplotlib.pyplot as plt
import numpy as np
import logging
from pylab import *
mpl.rcParams['font.sans-serif']=['STSong']

x_labels = ['G1', 'G2', 'G3', 'G4', 'G5'] 
y_left_title = 'Scores'
main_title = 'main title'
men_means = [20,34,30,35,27]      # data1
women_means = [25,32,34,20,25]    # data2


x = np.arange(len(x_labels))
width = 0.35

fig,ax = plt.subplots()
rects1 =ax.bar(x-width/2,men_means,width,label='Men')
rects2 =ax.bar(x+width/2,women_means,width,label='women')
ax.set_title(main_title)
ax.set_ylabel(y_left_title)

ax.set_xticks(x)
ax.set_xticklabels(x_labels)
ax.legend()

def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        ax.annotate('{}'.format(height),
                    xy=(rect.get_x() + rect.get_width() / 2, height),
                    xytext=(0,3),
                    textcoords= "offset points",
                    ha='center',va='bottom'
                    )

autolabel(rects1)
autolabel(rects2)

fig.tight_layout()
plt.show()

