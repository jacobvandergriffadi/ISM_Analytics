# import module
import streamlit as st
import pyodbc
import pandas as pd
import networkx as nx
import matplotlib.pyplot as plt
# Import date class from datetime module
from datetime import date
# Title
st.title("Lot Tracker")

name = st.text_input("Enter Lot Id", "Type Here ...")
 
# display the name when the submit button is clicked
# .title() is used to get the input text string
if(st.button('Submit')):
    result = name.title()
    st.success(result)

def get_network(lot_id):

    lot_id = "'" + lot_id + "'"
   
    cnxn = pyodbc.connect("Driver={SQL Server Native Client 11.0};"
                          "Server=dbinvreconprd.ad.analog.com\internal;"
                          "Database=InvRecon;"
                          "Trusted_Connection=yes;")


    cursor = cnxn.cursor()

    invrecon = pd.read_sql_query("SELECT * FROM utransactions WHERE TranCd = 'EOH' AND LotId =" +str(lot_id), cnxn)


    
    
    invrecon['LotAge'] = pd.to_datetime(date.today()) - pd.to_datetime(invrecon['Age'], errors='coerce')
    invrecon['LotAgeDays'] = invrecon['LotAge'].astype(str).str.split(' ', expand=True).iloc[:,0]


    def summary_statistics(df, node):

        import numpy as np

        stat_df = df.copy()   
        stat_df['LotAgeDays'] = pd.to_numeric(stat_df['LotAgeDays'], downcast="float", errors='coerce')

        recon_qty_stats = stat_df.groupby([node])['ReconQty'].agg([np.mean,np.median,np.std])
        lot_age_stats = stat_df.groupby([node])['LotAgeDays'].agg([np.mean,np.median,np.std])

        summary_stats = pd.merge(left=recon_qty_stats, right=lot_age_stats, left_index=True, right_index=True,how='left').reset_index()

        summary_stats = summary_stats.rename(columns={'mean_x':'ReconQty_Mean',
                                                  'median_x':'ReconQty_Median',
                                                  'std_x':'ReconQty_Std_Dev',
                                                  'mean_y':'Age_Mean',
                                                  'median_y':'Age_Median',
                                                  'std_y':'Age_Std_Dev'})
        return summary_stats

    sys_name_stats = summary_statistics(invrecon, 'SysName')
    prod_area_stats = summary_statistics(invrecon, 'ProdArea')
    part_name_stats = summary_statistics(invrecon, 'PartName')

    edges = invrecon[['Week', 'SysName', 'ProdArea', 'PartName', 'LotId','ReconQty']].sort_values(by='Week')
    for column in edges:
        try:
            edges[column] = edges[column].str.strip() 
        except:
            pass



    def edge_list_node(df, node):
        edges_list = pd.DataFrame(columns = ["week", "source", "target","weight"])
        for i in range(len(df)):
            try:
                week = df['Week'][i]

                next_week = df['Week'][i + 1]

                source = df[node][i] + ": " + str(week)

                target = df[node][i + 1] + ": " + str(next_week)

                weight = df['ReconQty'][i]

                edge_dict = {"week":[week], "source":[source],"target":[target], "weight":[weight]}
                edge = pd.DataFrame(data=edge_dict)
                edges_list = pd.concat([edges_list,edge])
            except:
                week = df['Week'][i]

                source = df[node][i] + ": " + str(week)

                target = df[node][i] + ": " + str(week)

                weight = df['ReconQty'][i]

                edge_dict = {"week":[week], "source":[source],"target":[target], "weight":[weight]}
                edge = pd.DataFrame(data=edge_dict)
            
                edges_list = pd.concat([edges_list,edge])
        edges_index = edges_list.set_index('week')
        return edges_index


    edge_G_prom_box = edge_list_node(edges, 'SysName')
    edge_G_prod_area = edge_list_node(edges, 'ProdArea')
    edge_G_promis_part = edge_list_node(edges, 'PartName')
    

    graphs = [edge_G_prom_box, edge_G_prod_area]
    titles = ["Promis Box Network", "Production Area Network"]

    title = -1

    for i in graphs:

        G = nx.from_pandas_edgelist(df=i, source='source', target='target',edge_attr='weight', create_using=nx.MultiDiGraph())
        pos = nx.spiral_layout(G, dim=2, resolution=5, equidistant=True, scale = 5)
        plt.figure(figsize=(18,10))
        nx.draw(G, pos,with_labels=True, font_size=10) 

        labels = dict([((u,v,),d['weight']) for u,v,d in G.edges(data=True)])

        nx.draw_networkx_nodes(G, pos, node_size=300) 

        nx.draw_networkx_edge_labels(G, pos, edge_labels=labels, alpha = 0.5)  

        title = title + 1
        
        plt.title(titles[title])
        plt.show()

get_network(result)
