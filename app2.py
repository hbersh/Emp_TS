import os
from datetime import date, datetime
import pandas as pd
import streamlit as st
import io

st.set_page_config(page_title="Employee Timesheet Tracker", page_icon="⏰", layout="wide")

# For cloud deployment, we'll use session state instead of local files
if 'timesheet_data' not in st.session_state:
    st.session_state.timesheet_data = None

def init_timesheet(start: date, end: date, employee_name: str) -> pd.DataFrame:
    dates = pd.date_range(start=start, end=end, freq="D")
    df = pd.DataFrame({
        "Date": dates,
        "Day": dates.strftime("%A"),
        "Hours Worked": [0.0] * len(dates),
        "Hourly Rate": [0.0] * len(dates),
        "Daily Total": [0.0] * len(dates),
        "Tasks Completed": ["" for _ in range(len(dates))],
    })
    df["Week"] = df["Date"].dt.isocalendar().week.astype(int)
    df["Month"] = df["Date"].dt.month_name()
    df["Employee Name"] = employee_name
    return df

def calculate_totals(df: pd.DataFrame) -> pd.DataFrame:
    df["Daily Total"] = df["Hours Worked"] * df["Hourly Rate"]
    return df

def main():
    st.title("⏰ Employee Timesheet Tracker")
    st.markdown("*Professional time tracking and payroll calculation system*")
    st.markdown("---")
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Setup")
        employee_name = st.text_input("Employee Name", value="Enter your name")
        
        col1, col2 = st.columns(2)
        with col1:
            start_date = st.date_input("Start Date", value=date.today())
        with col2:
            end_date = st.date_input("End Date", value=date(2025, 12, 31))
        
        if st.button("Initialize/Reset Timesheet"):
            st.session_state.timesheet_data = init_timesheet(start_date, end_date, employee_name)
            st.success("Timesheet initialized!")
        
        st.markdown("---")
        st.markdown("### 📋 Instructions")
        st.markdown("""
        1. Enter your name above
        2. Set your date range
        3. Fill in daily hours and rates
        4. Add task descriptions
        5. Export your data when ready
        """)
    
    # Initialize timesheet if not exists
    if st.session_state.timesheet_data is None:
        st.session_state.timesheet_data = init_timesheet(start_date, end_date, employee_name)
    
    df = st.session_state.timesheet_data.copy()
    
    # Main content area
    st.header(f"📊 Timesheet Dashboard - {employee_name}")
    
    # Display summary metrics
    col1, col2, col3, col4 = st.columns(4)
    
    total_hours = df["Hours Worked"].sum()
    total_earnings = df["Daily Total"].sum()
    avg_hourly_rate = df[df["Hourly Rate"] > 0]["Hourly Rate"].mean() if len(df[df["Hourly Rate"] > 0]) > 0 else 0
    days_worked = len(df[df["Hours Worked"] > 0])
    
    with col1:
        st.metric("Total Hours", f"{total_hours:.1f}")
    with col2:
        st.metric("Total Earnings", f"${total_earnings:.2f}")
    with col3:
        st.metric("Average Rate", f"${avg_hourly_rate:.2f}/hr")
    with col4:
        st.metric("Days Worked", days_worked)
    
    st.markdown("---")
    
    # Editable data table
    st.subheader("📝 Daily Time Entry")
    st.markdown("*Click on cells to edit your hours, rates, and task descriptions*")
    
    # Create editable dataframe
    edited_df = st.data_editor(
        df[["Date", "Day", "Hours Worked", "Hourly Rate", "Tasks Completed"]],
        use_container_width=True,
        num_rows="dynamic",
        column_config={
            "Date": st.column_config.DateColumn("Date", disabled=True),
            "Day": st.column_config.TextColumn("Day", disabled=True),
            "Hours Worked": st.column_config.NumberColumn("Hours Worked", min_value=0.0, max_value=24.0, step=0.5),
            "Hourly Rate": st.column_config.NumberColumn("Hourly Rate ($)", min_value=0.0, step=0.25),
            "Tasks Completed": st.column_config.TextColumn("Tasks & Notes", width="large")
        }
    )
    
    # Update the dataframe with edited values
    df.loc[:, "Hours Worked"] = edited_df["Hours Worked"]
    df.loc[:, "Hourly Rate"] = edited_df["Hourly Rate"] 
    df.loc[:, "Tasks Completed"] = edited_df["Tasks Completed"]
    
    # Calculate totals
    df = calculate_totals(df)
    st.session_state.timesheet_data = df
    
    # Weekly and Monthly summaries
    st.markdown("---")
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📅 Weekly Summary")
        weekly_summary = df.groupby("Week").agg({
            "Hours Worked": "sum",
            "Daily Total": "sum"
        }).round(2)
        weekly_summary.columns = ["Total Hours", "Total Earnings ($)"]
        st.dataframe(weekly_summary, use_container_width=True)
    
    with col2:
        st.subheader("📆 Monthly Summary")
        monthly_summary = df.groupby("Month").agg({
            "Hours Worked": "sum", 
            "Daily Total": "sum"
        }).round(2)
        monthly_summary.columns = ["Total Hours", "Total Earnings ($)"]
        st.dataframe(monthly_summary, use_container_width=True)
    
    # Export functionality
    st.markdown("---")
    st.subheader("💾 Export Your Data")
    st.markdown("*Download your timesheet data for payroll or record keeping*")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Export to Excel
        if st.button("📊 Prepare Excel Export"):
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                df.to_excel(writer, sheet_name='Daily Timesheet', index=False)
                weekly_summary.to_excel(writer, sheet_name='Weekly Summary')
                monthly_summary.to_excel(writer, sheet_name='Monthly Summary')
            
            st.download_button(
                label="⬇️ Download Excel File",
                data=output.getvalue(),
                file_name=f"timesheet_{employee_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
    
    with col2:
        # Export to CSV
        if st.button("📄 Prepare CSV Export"):
            csv = df.to_csv(index=False)
            st.download_button(
                label="⬇️ Download CSV File",
                data=csv,
                file_name=f"timesheet_{employee_name.replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv"
            )
    
    with col3:
        # Clear all data
        if st.button("🗑️ Clear All Data", type="secondary"):
            if st.button("⚠️ Confirm Clear", type="secondary"):
                st.session_state.timesheet_data = init_timesheet(start_date, end_date, employee_name)
                st.success("Data cleared!")
    
    # Footer
    st.markdown("---")
    st.markdown("*Built with Streamlit • Professional Timesheet Tracker*")

if __name__ == "__main__":
    main()
