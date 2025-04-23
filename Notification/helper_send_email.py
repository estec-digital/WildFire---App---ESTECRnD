# helper_send.py
def send_email_wrapper(args):
    from SendEmail import send_email  # import inside the function to avoid pickle issues
    try:
        send_email(*args)
    except Exception as e:
        import traceback
        print("\n\n   [EMAIL ERROR]", e)
        traceback.print_exc()
