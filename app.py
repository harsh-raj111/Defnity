# imports file 

from supabase import create_client 
import streamlit as st 
import pandas as pd
import plotly.express as px
import requests
import uuid
import os 
from dotenv import load_dotenv
# config

st.set_page_config(page_title='Defnity', page_icon=':bar_chart:', layout='wide')


# supabase setup
# load_dotenv()
# supabase_url = os.getenv("SUPABASE_URL")
# supabase_key = os.getenv("SUPABASE_KEY")
supabase_url = st.secrets["SUPABASE_URL"]
supabase_key = st.secrets["SUPABASE_KEY"]
supabase_client = create_client(supabase_url, supabase_key)
print(requests.get("https://aendrjdowanmdukuceeh.supabase.co").status_code)



# authentication 

def login():
    st.title("login/signup")
    tab1,tab2 = st.tabs(["Login","signup"])
    # login form 
    with tab1:
        email = st.text_input("email")
        password = st.text_input("password",type="password")
        if st.button("login"):
            res = supabase_client.auth.sign_in_with_password({"email":email,"password":password})
            if res.user:
                st.session_state.user = res.user
                st.success("logged in successfully")
                st.rerun()
            else:
                st.error("Invalid credentials")
    # signup form

    with tab2:
        email = st.text_input("email",key = "signup_email")
        password = st.text_input("password", type = "password" ,key = "signup_password")
        if st.button("create account"):
            res = supabase_client.auth.sign_up({"email":email,"password":password})
            if res.user:
                st.success("account created successfully!, Now login")
            else:
                st.error("signup failed")
            
# session check

if "user" not in st.session_state:
    st.session_state.user = None
if st.session_state.user is None:
    login()
    st.stop()



user_id = st.session_state.user.id






# uploading data 

st.title("Defnity Sales Analytics")
if st.button("logout"):
 st.session_state.user = None
 st.rerun()

uploaded_file = st.sidebar.file_uploader('Upload your file',type = ['csv','xlsx', 'xlsm'])
if uploaded_file is not None:
     try:
        if uploaded_file.name.endswith('.csv'):
            df = pd.read_csv(uploaded_file)
        elif uploaded_file.name.endswith('.xlsx') or uploaded_file.name.endswith('.xlsm'):
            df = pd.read_excel(uploaded_file)
        st.success('File uploaded successfully!')
        st.dataframe(df)
        columns = df.columns.tolist()
        def detect_column(columns,keywords):
            for column in columns:
                column_lower = column.lower()
                for keyword in keywords:
                    if keyword in column_lower:
                        return column
            return None
        
      #   smart keyword detection

        price_keywords = ['price','cost','amount','value','total','sale','revenue','income','profit']
        qty_keywords = ['quantity','qty','units','count']
        date_keywords = ['date','time','day','month','year','created','updated']
        product_keywords = ['product','item','name','description','category','type']
        cost_keywords = ['cost','expense','amount','price','value','expense','purchase','buy','cogs']

      #   detect columns

        auto_price = detect_column(columns,price_keywords)
        auto_qty = detect_column(columns,qty_keywords)
        auto_date = detect_column(columns,date_keywords)
        auto_product = detect_column(columns,product_keywords)
        auto_cost = detect_column(columns,cost_keywords)

      #   selectbox with default values 

        price_column = st.selectbox('select price column',columns,index=columns.index(auto_price) if auto_price else 0)
        qty_column = st.selectbox('select quantity column',columns,index=columns.index(auto_qty) if auto_qty else 0)
        date_column = st.selectbox('select date column',columns,index=columns.index(auto_date) if auto_date else 0)
        product_column = st.selectbox('select product column',columns,index=columns.index(auto_product) if auto_product else 0)
        cost_column = st.selectbox('select cost column (optional)',columns,index=columns.index(auto_cost) if auto_cost else 0)
        currency_symbol = st.text_input('Enter currency symbol (optional)', value='$')

      # data preprocessing

        df[date_column] = pd.to_datetime(df[date_column],errors='coerce')
        df[price_column] = pd.to_numeric(df[price_column],errors='coerce')
        df[qty_column] = pd.to_numeric(df[qty_column],errors = 'coerce')
        df[cost_column] = pd.to_numeric(df[cost_column],errors = 'coerce')
        df = df.dropna(subset=[price_column,date_column])
        def clean_numeric(df,col):
            df[col]=df[col].astype(str).str.replace(r'[^\d.]','',regex=True)
            df[col] = pd.to_numeric(df[col],errors = 'coerce')
            return df
        df = clean_numeric(df,price_column)
        if qty_column!= 'None':
            df = clean_numeric(df,qty_column)
            df[qty_column] = df[qty_column].fillna(1)
        else:
            df[qty_column] = 1
            qty_column = 'Quantity'
        df = df.drop_duplicates()
        if df.empty:
            st.error("No valid data found")
            st.stop()
        if df[price_column].isnull().all():
            st.error("No valid price data found")
            st.stop()
        start_date = df[date_column].min()
        end_date = df[date_column].max()
        st.write("Cleaned Data Preview:")
        st.write(f"Data covers from {start_date.date()} to {end_date.date()}")
        st.dataframe(df.head(20))

      # metrices
        if qty_column: 
            df['Total_revenue'] = df[price_column] * df[qty_column]
        else:
              df['Total_revenue'] = df[price_column]

        total_revenue = df['Total_revenue'].sum()
        total_sales = df[qty_column].sum()
        average_price = df[price_column].mean()
        highest_price = df[price_column].max()
        highest_selling_product = df.groupby(product_column)[qty_column].sum().idxmax()
        busy_month = df.groupby(date_column)[qty_column].sum().idxmax()
        Top_products_byRevenue  = df.groupby(product_column)[price_column].sum().sort_values(ascending=False).head(5)
        Top_products_bySales = df.groupby(product_column)[qty_column].sum().sort_values(ascending=False).head(5)
        df['Profit'] = (df[price_column]- df[cost_column])*df[qty_column]
        total_profit = df['Profit'].sum()
        total_loss = df[df['Profit']<0]['Profit'].sum()
        profit_margin = st.slider("Estimate profit margin (%)", 0, 100, 20)
        df['Estimated_profit'] = df['Total_revenue']*(profit_margin/100)
        total_estimated_profit = df['Estimated_profit'].sum()
        total_loss = 0

        # csv export 
        summary_data = {
            "Metric":[
                "Total Revenue",
                "Total Sales",
                "Average Price",
                "Highest Price",
                "total profit",
                "total loss",
                "Top Product by Revenue",
                "Top Product by Sales",
                "Start Date",
                "End Date"
            ],
            "Value":[
                f'{currency_symbol}{total_revenue:,.2f}',
                int(total_sales),
                f'{currency_symbol}{average_price:,.2f}',
                f'{currency_symbol}{highest_price:,.2f}',
                f'{currency_symbol}{total_profit:,.2f}',
                f'{currency_symbol}{total_loss:,.2f}',
                
                Top_products_byRevenue.index[0],
                Top_products_bySales.index[0],
                str(df[date_column].min().date()),
                str(df[date_column].max().date())
            ]
        }
        summary_df = pd.DataFrame(summary_data)
        top_products_Df = Top_products_byRevenue.reset_index()
        top_products_Df.columns = [product_column,'Revenue']
        final_export = pd.concat([summary_df,pd.DataFrame([{}]),top_products_Df],ignore_index=True)
        csv = final_export.to_csv(index=False).encode('utf-8')
        st.download_button(
            label = "Download csv",
            data = csv,
            file_name = "Defnity_cleaned_sales_report.csv",
            mime = "text/csv"

        )
      #   kpis

        col1,col2,col3 , col4  = st.columns(4)
        with col1:
            st.metric('Total Revenue',f'{currency_symbol}{total_revenue:,.2f}')
        with col2:
            st.metric('Total Sales',f'{total_sales:,.0f}')
        with col3:
            st.metric('Average Price',f'{currency_symbol}{average_price:,.2f}')
        with col4:
            st.metric('Highest Price',f'{currency_symbol}{highest_price:,.2f}')
        

        col5 , col6 , col7 ,col8 = st.columns(4)
        with col5:
            st.metric('Total Profit',f'{currency_symbol}{total_profit:,.2f}')
        with col6:
            st.metric('Total Loss',f'{currency_symbol}{total_loss:,.2f}')
        with col7:
            st.metric('Estimated Profit',f'{currency_symbol}{total_estimated_profit:,.2f}')
        with col8:
            st.metric('Profit Margin',f'{profit_margin}%')

         # graphs 

        col5,col6 = st.columns(2)
        fig1 = px.bar(df.groupby(date_column)['Total_revenue'].sum().reset_index(),x=date_column,y='Total_revenue',title='Revenue Over Time')
        if qty_column:
         fig2 = px.bar(df.groupby(product_column)[qty_column].sum().reset_index(),x=product_column,y=qty_column,title='Sales by Product')
        col5.plotly_chart(fig1,use_container_width=True)
        col6.plotly_chart(fig2,use_container_width=True)
        df['Month'] = df[date_column].dt.to_period('M').astype(str)
        monthly = df.groupby('Month')['Total_revenue'].sum().reset_index()
        fig3 = px.line(monthly,x='Month',y='Total_revenue',title='Monthly Revenue Trend')
        st.plotly_chart(fig3,use_container_width=True)
        daily = df.groupby(date_column)['Total_revenue'].sum()
        best_day = daily.idxmax()
        worst_day = daily.idxmin()
        st.info(f"Best day for sales was {best_day.date()} and worst day was {worst_day.date()}")
        monthly['growth'] = monthly['Total_revenue'].pct_change()*100
        avg_growth = monthly['growth'].mean()
        if avg_growth > 0:
            st.success(f"Average monthly growth is {avg_growth:.2f}% which is positive")
        elif avg_growth < 0:
            st.warning(f"Average monthly growth is {avg_growth:.2f}% which is negative")
        else:
            st.info("Average monthly growth is 0% which is stable")
        if total_profit > 0 or total_estimated_profit > 0:
            st.success("Overall profitable business")
        else:
            st.error("Overall loss making business")
        best_month = monthly.loc[monthly['Total_revenue'].idxmax()]
        st.info(f"Best month:{best_month['Month']} with  revenue of {best_month['Total_revenue']:.2f}")
        col7,col8 = st.columns(2)
        with col7:
            st.subheader('Top 5 Products by Revenue')
            st.dataframe(Top_products_byRevenue)
            
        with col8:
            st.subheader('Top 5 Products by Sales')
            st.dataframe(Top_products_bySales)

        pareto = df.groupby(product_column)['Total_revenue'].sum().sort_values(ascending=False)
        pareto_cum = pareto.cumsum()
        pareto_per = pareto_cum/pareto.sum() *100
        pareto_df = pareto.reset_index()
        pareto_df['cum_perc'] = pareto_per.values
        top_n = (pareto_df["cum_perc"]<=80).sum()
        st.subheader('Pareto Analysis')
        st.dataframe(pareto_df.head(top_n))
        st.info(f"Top {top_n} products contribute to 80% of revenue")
        
       
        best_product = df.groupby(product_column)['Total_revenue'].sum().idxmax()
        worst_product = df.groupby(product_column)['Total_revenue'].sum().idxmin()
        top_rev_name = Top_products_byRevenue.index[0]
        Top_sales_name = Top_products_bySales.index[0]
        if top_rev_name != Top_sales_name:
            st.info(f"{Top_sales_name} sells most but  {top_rev_name} earns most revenue.")
        
        # save to db 
       
        data = {
        "user_id": user_id,
        "Total_revenue": float(total_revenue),
        "Total_sales": int(total_sales),
        "Top_product": str(highest_selling_product),
        "Start_date": str(df[date_column].min()),
        "End_date": str(df[date_column].max())
}

       
        if st.button("saved report"):
         try:
          supabase_client.table("defnity_reports").insert(data).execute()
          st.success("Report saved to database ✅")
         except Exception as e:
          st.error(f"Error saving report: {e}")

       

     
        
     except Exception as e:
       st.error(f'Error occurred while reading the file: {e}')