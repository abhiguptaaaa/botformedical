import os
import fitz  # PyMuPDF
import tempfile
import logging
from telegram import Update, InputFile, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, ConversationHandler, CallbackContext
)

# Enable logging
logging.basicConfig(level=logging.INFO)

# Path to your certificate template
TEMPLATE_PATH = os.path.join(os.getcwd(), 'pdf_templates', 'certificate_template_with_fields.pdf')

# Define conversation states
MAIN_MENU, PATIENT_NAME, PATIENT_AGE, PATIENT_GENDER, TEST_DATE, REPORT_DATE, REFERRING_DOCTOR, SIGNING_DOCTOR = range(8)

# Define keyboard layouts
def get_main_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("🏥 Generate Medical Certificate")]
    ], resize_keyboard=True)

def get_gender_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("👨 Male"), KeyboardButton("👩 Female")],
        [KeyboardButton("⚧️ Other"), KeyboardButton("❌ Cancel")]
    ], resize_keyboard=True)

def get_cancel_keyboard():
    return ReplyKeyboardMarkup([
        [KeyboardButton("❌ Cancel")]
    ], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 Welcome to the Medical Certificate Generator Bot!\n\n"
        "Use the buttons below to navigate.",
        reply_markup=get_main_keyboard()
    )
    return MAIN_MENU

async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if "Generate Medical Certificate" in text:
        await update.message.reply_text(
            "👤 What's the patient's name?",
            reply_markup=get_cancel_keyboard()
        )
        return PATIENT_NAME
    else:
        await update.message.reply_text(
            "Please use the available buttons.",
            reply_markup=get_main_keyboard()
        )
        return MAIN_MENU

async def patient_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Cancel":
        return await cancel(update, context)
    
    context.user_data['patient_name'] = update.message.text
    await update.message.reply_text(
        "📅 Please enter the patient's age:",
        reply_markup=get_cancel_keyboard()
    )
    return PATIENT_AGE

async def patient_age(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Cancel":
        return await cancel(update, context)
    
    context.user_data['patient_age'] = update.message.text
    await update.message.reply_text(
        "⚧️ What is the patient's gender?",
        reply_markup=get_gender_keyboard()
    )
    return PATIENT_GENDER

async def patient_gender(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Cancel":
        return await cancel(update, context)
    
    # Extract gender from button click
    gender_text = update.message.text
    if "Male" in gender_text:
        context.user_data['patient_gender'] = "Male"
    elif "Female" in gender_text:
        context.user_data['patient_gender'] = "Female"
    elif "Other" in gender_text:
        context.user_data['patient_gender'] = "Other"
    else:
        context.user_data['patient_gender'] = gender_text
    
    await update.message.reply_text(
        "🩺 Enter the test date (YYYY-MM-DD):",
        reply_markup=get_cancel_keyboard()
    )
    return TEST_DATE

async def test_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Cancel":
        return await cancel(update, context)
    
    context.user_data['test_date'] = update.message.text
    await update.message.reply_text(
        "📝 Enter the report date (YYYY-MM-DD):",
        reply_markup=get_cancel_keyboard()
    )
    return REPORT_DATE

async def report_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Cancel":
        return await cancel(update, context)
    
    context.user_data['report_date'] = update.message.text
    await update.message.reply_text(
        "👨‍⚕️ Enter the referring doctor's name:",
        reply_markup=get_cancel_keyboard()
    )
    return REFERRING_DOCTOR

async def referring_doctor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Cancel":
        return await cancel(update, context)
    
    context.user_data['referring_doctor'] = update.message.text
    await update.message.reply_text(
        "👩‍⚕️ Enter the signing doctor's name:",
        reply_markup=get_cancel_keyboard()
    )
    return SIGNING_DOCTOR

async def signing_doctor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.text == "❌ Cancel":
        return await cancel(update, context)
    
    context.user_data['signing_doctor'] = update.message.text
    await update.message.reply_text("🔧 Generating your certificate... please wait!")
    await generate_and_send_pdf(update, context)
    
    # Return to main menu after completion
    await update.message.reply_text(
        "✅ Certificate generated successfully! What would you like to do next?",
        reply_markup=get_main_keyboard()
    )
    return MAIN_MENU

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '❌ Operation cancelled. What would you like to do?',
        reply_markup=get_main_keyboard()
    )
    return MAIN_MENU

def get_pdf_fields(pdf_path):
    """Extract PDF form fields."""
    doc = fitz.open(pdf_path)
    fields = {}
    for page in doc:
        widgets = page.widgets()
        for widget in widgets:
            field_name = widget.field_name
            fields[field_name] = widget
    doc.close()
    return fields

def fill_pdf_template(template_path, data, output_path):
    """Fill the PDF template."""
    doc = fitz.open(template_path)
    for page in doc:
        widgets = page.widgets()
        for widget in widgets:
            field_name = widget.field_name
            value_to_set = data.get(field_name)
            if value_to_set:
                widget.field_value = value_to_set
                widget.update()
    doc.save(output_path)
    doc.close()

async def generate_and_send_pdf(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Generate the PDF and send to user."""
    form_data = context.user_data

    # Map form fields to PDF fields
    pdf_data = {
        'text_2hcpn': form_data.get('patient_name', ''),
        'text_3ydqz': form_data.get('test_date', ''),
        'text_4ybok': form_data.get('report_date', ''),
        'text_5rysh': form_data.get('referring_doctor', ''),
        'text_6njmy': form_data.get('patient_name', ''),
        'text_11aaku': form_data.get('signing_doctor', ''),
        'text_10vfgg': form_data.get('test_date', ''),
        'text_7wpva': form_data.get('patient_age', ''),
        'text_8uoj': form_data.get('referring_doctor', ''),
        'text_9quis': form_data.get('report_date', ''),
        'text_11ikbs': form_data.get('signing_doctor', ''),
    }

    # Add gender field if available
    if 'patient_gender' in form_data:
        pdf_data['text_gender'] = form_data.get('patient_gender', '')

    # Create a temp file
    temp_output = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
    output_path = temp_output.name
    temp_output.close()

    try:
        fill_pdf_template(TEMPLATE_PATH, pdf_data, output_path)

        # Open the file in binary mode and send with proper MIME type
        with open(output_path, 'rb') as pdf_file:
            await update.message.reply_document(
                document=InputFile(pdf_file, filename="medical_certificate.pdf"),
                caption="📄 Here's your medical certificate"
            )
    except Exception as e:
        logging.error(f"Error generating PDF: {str(e)}")
        await update.message.reply_text(f"❌ Error generating PDF: {str(e)}")
    finally:
        # Clean up
        if os.path.exists(output_path):
            os.remove(output_path)

def main():
    application = ApplicationBuilder().token('7766682700:AAHwEmX6s1D4p4S22Llu4L17xMvQPMIzU28').build()

    conv_handler = ConversationHandler(
        entry_points=[
            CommandHandler('start', start),
            MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu)
        ],
        states={
            MAIN_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, main_menu)],
            PATIENT_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, patient_name)],
            PATIENT_AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, patient_age)],
            PATIENT_GENDER: [MessageHandler(filters.TEXT & ~filters.COMMAND, patient_gender)],
            TEST_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, test_date)],
            REPORT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, report_date)],
            REFERRING_DOCTOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, referring_doctor)],
            SIGNING_DOCTOR: [MessageHandler(filters.TEXT & ~filters.COMMAND, signing_doctor)],
        },
        fallbacks=[CommandHandler('cancel', cancel)],
    )

    application.add_handler(conv_handler)
    application.run_polling()

if __name__ == '__main__':
    main()