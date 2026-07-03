import sys
import numpy as np
import pandas as pd
import matplotlib
import sklearn
import scipy

print("Python:", sys.version)
print("NumPy:", np.__version__)
print("Pandas:", pd.__version__)
print("Matplotlib:", matplotlib.__version__)
print("Scikit-learn:", sklearn.__version__)
print("SciPy:", scipy.__version__)

x = np.array([1, 2, 3, 4, 5])
print("Array mean:", x.mean())
print("Python research stack OK")
