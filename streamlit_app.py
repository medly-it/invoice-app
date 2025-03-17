import streamlit as st
from fpdf import FPDF
from datetime import datetime, timedelta, timezone

# Define UTC+7 timezone
utc7 = timezone(timedelta(hours=7))

def generate_invoice_pdf2(logo_path,
                          company_address,
                          invoice_id,
                          agent_id,
                          agent_name,
                          patient_data_list):
    """
    Generate a PDF invoice with the given details.
    Returns the PDF as bytes.
    """
    pdf = FPDF(orientation='P', unit='mm', format='A4')
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.set_margins(left=10, top=15, right=10)

    # Add Company Logo from a fixed location
    if logo_path:
        pdf.image(logo_path, x=10, y=5, w=40)

    pdf.set_font("Arial", "B", 14)
    pdf.ln(20)

    # Optionally, display Company Address if needed
    # pdf.multi_cell(0, 10, company_address, border=0, align="L")
    pdf.ln(2)

    # Date & Invoice ID using UTC+7
    pdf.set_font("Arial", size=12)
    current_date = datetime.now(utc7).strftime("%d-%m-%Y")
    pdf.cell(0, 10, f"Date: {current_date}", ln=True)
    pdf.cell(0, 10, f"Invoice ID: {invoice_id}", ln=True)

    # Agent Details
    pdf.cell(0, 10, f"Agent ID: {agent_id}", ln=True)
    pdf.cell(0, 10, f"Pay Commission to: {agent_name}", ln=True)
    pdf.ln(5)

    # Table Header
    pdf.set_font("Arial", "B", 10)
    col_widths = [10, 80, 80]
    table_header = [
        "No.",
        "Patient Name",
        "Comm. ATax"
    ]
    for width, header in zip(col_widths, table_header):
        pdf.cell(width, 8, header, border=1, align="C")
    pdf.ln(8)

    # Table Content
    pdf.set_font("Arial", size=10)
    total_commission_after_tax = 0.0

    for idx, data in enumerate(patient_data_list, start=1):
        patient_name = data["patient_name"]
        commission_to_agent_after_tax = data["commission_to_agent_after_tax"]
        total_commission_after_tax += commission_to_agent_after_tax

        row_data = [
            str(idx),
            patient_name,
            f"{commission_to_agent_after_tax:,.2f}"
        ]

        for width, cell in zip(col_widths, row_data):
            align = 'R' if cell.replace('.', '').replace(',', '').isdigit() else 'L'
            pdf.cell(width, 8, cell, border=1, align=align)
        pdf.ln(8)

    # Grand Total: Total Commission After Tax
    pdf.set_font("Arial", "B", 10)
    pdf.cell(0, 10, f"Total Commission After Tax (IDR): {total_commission_after_tax:,.2f}", ln=True)
    pdf.cell(0, 12, f"Notes:", ln=True)
    pdf.cell(0, 13, f"Tax Rate: 10 %", ln=True)

    pdf_bytes = pdf.output(dest="S").encode("latin1")
    return pdf_bytes

st.title("Invoice PDF Generator")

# Place the number of patients input outside the form to allow dynamic re-rendering.
number_patients = st.number_input("Number of Patients", min_value=1, value=1, step=1)

with st.form("invoice_form"):
    st.header("Invoice Details")
    # Auto-generate the invoice ID based on current datetime in UTC+7
    invoice_id = datetime.now(utc7).strftime("%Y%m%d%H%M%S")
    st.markdown(f"**Generated Invoice ID:** `{invoice_id}`")
    
    agent_id = st.text_input("Agent ID")
    agent_name = st.text_input("Agent Name")
    company_address = st.text_area("Company Address", 
                                   value="MEDLY PELITA ABADI\nMedan, Indonesia\nPhone: +62-852-1821-8233")
    
    # Fixed logo path: make sure 'assets/logo.png' exists in your project directory.
    fixed_logo_path = "assets/logo.png"
    st.markdown(f"**Using fixed logo:** `{fixed_logo_path}`")
    
    st.header("Patient Details")
    patient_details = []
    for i in range(int(number_patients)):
        st.markdown(f"#### Patient {i+1}")
        patient_name = st.text_input(f"Patient {i+1} Name", key=f"patient_name_{i}")
        bill_amount = st.number_input(f"Patient {i+1} Bill Amount (RM)", key=f"bill_amount_{i}",
                                      min_value=0.0, format="%.2f")
        excluded_bill = st.number_input(f"Patient {i+1} Excluded Bill Amount (RM)", key=f"excluded_bill_{i}",
                                        min_value=0.0, format="%.2f")
        rm_to_idr_rate = st.number_input(f"Patient {i+1} RM to IDR Rate", key=f"rate_{i}",
                                         min_value=0.0, format="%.2f")
        commission_percent = st.number_input(f"Patient {i+1} Commission Percentage (e.g. 0.1 for 10%)",
                                             key=f"commission_{i}", min_value=0.0, format="%.2f")
        patient_details.append({
            "patient_name": patient_name,
            "bill_amount_rm": bill_amount,
            "excluded_bill_rm": excluded_bill,
            "rm_to_idr_rate": rm_to_idr_rate,
            "commission_percent": commission_percent
        })

    submitted = st.form_submit_button("Generate Invoice")

if submitted:
    # Calculate patient-specific values for PDF generation
    patient_data_list = []
    for patient in patient_details:
        total_bill_idr = patient["bill_amount_rm"] * patient["rm_to_idr_rate"]
        excluded_bill_idr = patient["excluded_bill_rm"] * patient["rm_to_idr_rate"]
        nett_amount = total_bill_idr - excluded_bill_idr
        commission_before_tax = nett_amount * patient["commission_percent"]
        commission_after_tax = commission_before_tax * 0.90
        commission_to_agent_after_tax = commission_after_tax / 2

        patient_data_list.append({
            "patient_name": patient["patient_name"],
            "total_bill_idr": total_bill_idr,
            "excluded_bill_idr": excluded_bill_idr,
            "nett_amount": nett_amount,
            "commission_percent": patient["commission_percent"],
            "commission_before_tax": commission_before_tax,
            "commission_after_tax": commission_after_tax,
            "commission_to_agent_after_tax": commission_to_agent_after_tax
        })

    # Generate the PDF invoice
    pdf_bytes = generate_invoice_pdf2(
        logo_path=fixed_logo_path,
        company_address=company_address,
        invoice_id=invoice_id,
        agent_id=agent_id,
        agent_name=agent_name,
        patient_data_list=patient_data_list
    )

    file_name = f"invoice_{invoice_id}_{agent_id}_{agent_name}.pdf"
    st.download_button(
        label="Download Invoice PDF",
        data=pdf_bytes,
        file_name=file_name,
        mime="application/pdf"
    )
