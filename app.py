import streamlit as st
import numpy as np 
import pandas as pd
import plotly.express as px

# إعدادات الصفحة - يجب أن تكون أول أمر Streamlit في الكود
st.set_page_config(page_title="Care_Stat Dashboard", layout="wide")
st.title("🏥 Care_Stat Dashboard")

# استخدام الديكور @st.cache_data لتسريع تحميل البيانات عند إعادة تشغيل السكربت
@st.cache_data
def load_data():
    """
    هذه الدالة مسؤولة عن تحميل وتنظيف البيانات من ملف CSV.
    """
    # --- التعديل الرئيسي هنا ---
    # تم تغيير المسار المطلق إلى مسار نسبي.
    # هذا يتطلب أن يكون ملف "Care_stat.csv" في نفس مجلد ملف البايثون (app.py).
    file_path = "Care_stat.csv"
    df = None 
    
    try:
        # قراءة ملف CSV مباشرة
        df = pd.read_csv(file_path, header=0, on_bad_lines="skip", encoding="utf-8")

    except FileNotFoundError:
        # عرض رسالة خطأ واضحة إذا لم يتم العثور على الملف وإيقاف التطبيق
        st.error(f"ERROR: The file '{file_path}' was not found.")
        st.error("Please make sure the file exists in the same directory as the script (app.py).")
        st.stop() # إيقاف تنفيذ الكود
    except Exception as e:
        st.error(f"An error occurred while reading the file: {e}")
        st.stop()

    # --- قسم تنظيف البيانات ---
    
    # تحويل الأعمدة الرقمية إلى النوع الرقمي، مع تحويل الأخطاء إلى قيم فارغة (NaN)
    numeric_cols = ["salary", "prescription_cost", "amount", "num_staff", 
                    "years_of_experience", "age", "age_patient", "visits_count"]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # تحويل أعمدة التاريخ إلى النوع الزمني، مع تحويل الأخطاء إلى قيم فارغة (NaT)
    date_cols = ["appointment_date", "record_date", "payment_date", "visit_date"]
    for col in date_cols:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")

    # إنشاء عمود جديد للشهر والسنة إذا كان عمود تاريخ الدفع موجودًا
    if "payment_date" in df.columns:
        df["month_year"] = df["payment_date"].dropna().dt.to_period("M").astype(str)

    return df

# تحميل البيانات باستخدام الدالة التي أنشأناها
df = load_data()

# --- واجهة المستخدم (UI) ---

st.header("Dashboard Tabs")

# إنشاء ثلاثة تبويبات رئيسية
tab1, tab2, tab3 = st.tabs(["🧑‍⚕️ Organization Overview", "🩺 Patient & Treatment Data", "💳 Financial Performance"])

# --- التبويب الأول: نظرة عامة على المؤسسة ---
with tab1:
    st.header("🧑‍⚕️ Hospital Overview")

    # إنشاء فلاتر في ثلاثة أعمدة
    col1, col2, col3 = st.columns(3)
    with col1:
        dept_list = ["All"] + list(df["department_name"].dropna().unique())
        selected_dept = st.selectbox("Select Department", dept_list, key="tab1_dept")
    with col2:
        gender_list = ["All"] + list(df["gender"].dropna().unique())
        selected_gender = st.selectbox("Select Gender", gender_list, key="tab1_gender")
    with col3:
        country_list = ["All"] + list(df["country"].dropna().unique())
        selected_country = st.selectbox("Select Country", country_list, key="tab1_country")

    # تطبيق الفلاتر على نسخة من البيانات
    filtered_df_tab1 = df.copy()
    if selected_dept != "All":
        filtered_df_tab1 = filtered_df_tab1[filtered_df_tab1["department_name"] == selected_dept]
    if selected_gender != "All":
        filtered_df_tab1 = filtered_df_tab1[filtered_df_tab1["gender"] == selected_gender]
    if selected_country != "All":
        filtered_df_tab1 = filtered_df_tab1[filtered_df_tab1["country"] == selected_country]

    # عرض مؤشرات الأداء الرئيسية (KPIs)
    st.subheader("Key Performance Indicators")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Employees", filtered_df_tab1["doctor_id"].nunique())
    k2.metric("Average Salary", f"{filtered_df_tab1['salary'].mean():,.0f}" if not filtered_df_tab1["salary"].empty else "N/A")
    k3.metric("Number of Departments", filtered_df_tab1["department_name"].nunique())
    if not filtered_df_tab1.empty and not filtered_df_tab1["gender"].empty:
        female_percentage = (filtered_df_tab1["gender"] == "female").mean() * 100
        k4.metric("Female Staff %", f"{female_percentage:.1f}%")
    else:
        k4.metric("Female Staff %", "N/A")

    # عرض الرسومات البيانية
    st.subheader("Visualizations")
    c1, c2 = st.columns(2)
    with c1:
        dept_count = filtered_df_tab1["department_name"].value_counts().reset_index()
        fig1 = px.bar(dept_count, x="count", y="department_name", orientation="h", title="Employee Count by Department")
        st.plotly_chart(fig1, use_container_width=True)
    with c2:
        fig2 = px.pie(filtered_df_tab1, names="gender", title="Gender Distribution")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.subheader("Average Salary by Department")
    salary_by_dept = filtered_df_tab1.groupby("department_name")["salary"].mean().reset_index()
    fig3 = px.bar(salary_by_dept, x="salary", y="department_name", orientation="h", title="Average Salary")
    st.plotly_chart(fig3, use_container_width=True)

# --- التبويب الثاني: بيانات المرضى والعلاج ---
with tab2:
    st.header("🩺 Patient & Treatment Data")
    
    # فلاتر خاصة بالتبويب الثاني
    disease_list = ["All"] + list(df["disease_name"].dropna().unique())
    selected_disease = st.selectbox("Select Disease", disease_list, key="tab2_disease")
    
    severity_list = ["All"] + list(df["severity_level"].dropna().unique())
    selected_severity = st.selectbox("Select Severity", severity_list, key="tab2_severity")

    # تطبيق الفلاتر
    filtered_df_tab2 = df.copy()
    if selected_disease != "All":
        filtered_df_tab2 = filtered_df_tab2[filtered_df_tab2["disease_name"] == selected_disease]
    if selected_severity != "All":
        filtered_df_tab2 = filtered_df_tab2[filtered_df_tab2["severity_level"] == selected_severity]

    # عرض مؤشرات الأداء الرئيسية
    st.subheader("Key Performance Indicators")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Patients", filtered_df_tab2["patient_id"].nunique())
    k2.metric("Most Common Disease", filtered_df_tab2["disease_name"].mode()[0] if not filtered_df_tab2.empty and not filtered_df_tab2["disease_name"].mode().empty else "N/A")
    k3.metric("Average Cost", f"{filtered_df_tab2['prescription_cost'].mean():,.2f}" if not filtered_df_tab2.empty else "N/A")
    k4.metric("Unique Medical Devices", filtered_df_tab2["equipment_name"].nunique())

    # عرض الرسومات البيانية
    st.subheader("Visualizations")
    c1, c2 = st.columns(2)
    with c1:
        disease_count = filtered_df_tab2["disease_name"].value_counts().head(10).reset_index()
        fig1 = px.bar(disease_count, x="count", y="disease_name", orientation="h", title="Top 10 Most Common Diseases")
        st.plotly_chart(fig1, use_container_width=True)
    with c2:
        fig2 = px.pie(filtered_df_tab2, names="severity_level", title="Disease Severity Distribution")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.subheader("Average Cost by Disease")
    cost_by_disease = filtered_df_tab2.groupby("disease_name")["prescription_cost"].mean().reset_index()
    fig3 = px.bar(cost_by_disease, x="prescription_cost", y="disease_name", orientation="h", title="Average Cost")
    st.plotly_chart(fig3, use_container_width=True)

# --- التبويب الثالث: الأداء المالي ---
with tab3:
    st.header("💳 Financial Performance")
    
    # فلاتر خاصة بالتبويب الثالث
    status_list = ["All"] + list(df["payment_status"].dropna().unique())
    selected_status = st.selectbox("Payment Status", status_list, key="tab3_status")
    
    method_list = ["All"] + list(df["method"].dropna().unique())
    selected_method = st.selectbox("Payment Method", method_list, key="tab3_method")

    # تطبيق الفلاتر
    filtered_df_tab3 = df.copy()
    if selected_status != "All":
        filtered_df_tab3 = filtered_df_tab3[filtered_df_tab3["payment_status"] == selected_status]
    if selected_method != "All":
        filtered_df_tab3 = filtered_df_tab3[filtered_df_tab3["method"] == selected_method]

    # عرض مؤشرات الأداء الرئيسية
    st.subheader("Key Performance Indicators")
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total Revenue", f"{filtered_df_tab3['amount'].sum():,.0f}" if not filtered_df_tab3.empty else "N/A")
    k2.metric("Average Transaction", f"{filtered_df_tab3['amount'].mean():,.2f}" if not filtered_df_tab3.empty else "N/A")
    if not filtered_df_tab3.empty and not filtered_df_tab3["payment_status"].empty:
        completed_percentage = (filtered_df_tab3["payment_status"] == "completed").mean() * 100
        k3.metric("Successful Payments %", f"{completed_percentage:.1f}%")
    else:
        k3.metric("Successful Payments %", "N/A")
    k4.metric("Most Common Method", filtered_df_tab3["method"].mode()[0] if not filtered_df_tab3.empty and not filtered_df_tab3["method"].mode().empty else "N/A")

    # عرض الرسومات البيانية
    st.subheader("Visualizations")
    c1, c2 = st.columns(2)
    with c1:
        fig1 = px.pie(filtered_df_tab3, names="payment_status", title="Payment Status Distribution")
        st.plotly_chart(fig1, use_container_width=True)
    with c2:
        fig2 = px.pie(filtered_df_tab3, names="method", title="Payment Method Distribution")
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")
    st.subheader("Monthly Revenue")
    if "month_year" in filtered_df_tab3.columns and not filtered_df_tab3["month_year"].dropna().empty:
        revenue_by_month = filtered_df_tab3.groupby("month_year")["amount"].sum().reset_index()
        fig3 = px.line(revenue_by_month, x="month_year", y="amount", title="Revenue by Month")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.warning("Not enough date information to display monthly revenue.")



