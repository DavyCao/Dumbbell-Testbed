import pandas as pd
from sklearn.tree import DecisionTreeClassifier
from sklearn.model_selection import train_test_split
from sklearn.tree import export_graphviz
from sklearn.externals.six import StringIO
from sklearn import metrics
from pprint import pprint
import csv
from IPython.display import Image
import pydotplus


df = pd.read_csv("tbf-exp-190402_200224.csv")
print(df)

bbrGoodput = {}
cubicGoodput = {}
decision = {}

rows, cols = df.shape
for i in range(rows):
    rowData = df.iloc[i]
    key = str(rowData[' Delay']) + "-" + str(rowData[' BW']) + "-" + str(rowData[' Limit'])

    if rowData['CC'] == 'bbr':
        bbrGoodput[key] = rowData[' Goodput(bps)']
    elif rowData['CC'] == 'cubic':
        cubicGoodput[key] = rowData[' Goodput(bps)']


for k in bbrGoodput.keys():
    if k in cubicGoodput.keys():
        if bbrGoodput[k] < cubicGoodput[k]:
            decision[k] = 'cubic'
        else:
            decision[k] = 'bbr'


# Creating the decision tree (csv)
csvname = "tbf-exp-190402_200224-decisionTree.csv"
csvfile = open(csvname, 'w')
writer = csv.writer(csvfile)
header = ['Delay(ms)', 'BW(mbps)', 'Buffer(bytes)', 'Decision']
writer.writerow(header)

for k in decision.keys():
    tokens = k.split('-')
    record = [tokens[0], tokens[1], tokens[2], decision[k]]
    writer.writerow(record)

csvfile.close()

# Creating the decision tree (model)
df_Dtree = pd.read_csv("tbf-exp-190402_200224-decisionTree.csv")
feature_cols = ['Delay(ms)', 'BW(mbps)', 'Buffer(bytes)']
X = df_Dtree[feature_cols]
y = df_Dtree.Decision

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.3, random_state=1)

clf = DecisionTreeClassifier()
clf = clf.fit(X_train,y_train)
y_pred = clf.predict(X_test)

print("Accuracy:",metrics.accuracy_score(y_test, y_pred))

# Plot
dot_data = StringIO()

export_graphviz(clf, out_file=dot_data,
                filled=True, rounded=True,
                special_characters=True,
                feature_names=feature_cols,
                max_depth=5,
                class_names=clf.classes_
                )

graph = pydotplus.graph_from_dot_data(dot_data.getvalue())
graph.write_png('decisionTree.png')
Image(graph.create_png())
