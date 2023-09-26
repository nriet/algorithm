import pandas as pd
import matplotlib.pyplot as plt
d = {'series a' : pd.Series([1., 2., 3.], index=['a', 'b', 'c']),
'series b' : pd.Series([1., 2., 3., 4.], index=['a', 'b', 'c', 'd'])}
df = pd.DataFrame(d)
title_string = "This is the title"
subtitle_string = "This is the subtitle"
plt.figure()
df.plot(kind='bar')
plt.suptitle(title_string, y=1.05, fontsize=18)
plt.title(subtitle_string, fontsize=10)
plt.show()