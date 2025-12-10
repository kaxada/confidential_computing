# main.py
# Updated entry point with policy token support

from chatbot import Chatbot
from policy_token import create_default_token
import config
import logging
import os
import argparse

os.makedirs(os.path.dirname(config.DEFAULT_LOG_PATH), exist_ok=True)

logging.basicConfig(
    filename=config.DEFAULT_LOG_PATH, 
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def main():
    """
    Initializes the chatbot and runs the main conversation loop.
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Privacy-preserving healthcare information assistant")
    parser.add_argument(
        "--role", 
        type=str, 
        default=config.DEFAULT_ROLE,
        choices=["pi", "admin", "researcher", "clinician", "analyst", "auditor", "student", "intern"],
        help="User role for KB access control"
    )
    parser.add_argument(
        "--privacy-level",
        type=str,
        default=None,
        choices=["none", "low", "moderate", "high"],
        help="Privacy level for differential privacy (defaults to role's assigned level)"
    )
    parser.add_argument(
        "--user-id",
        type=str,
        default="cli_user",
        help="User identifier"
    )
    parser.add_argument(
        "--provider",
        type=str,
        default=config.LLM_PROVIDER,
        choices=["openai", "gemini"],
        help="LLM provider (openai or gemini)"
    )
    
    args = parser.parse_args()

    # Determine privacy level: explicitly provided > role default > system default
    if args.privacy_level is None:
        args.privacy_level = config.ROLE_PRIVACY_LEVEL.get(args.role, config.DEFAULT_PRIVACY_LEVEL)
    
    # Create policy token based on CLI arguments
    policy_token = create_default_token(
        privacy_level=args.privacy_level,
        role=args.role
    )
    policy_token.user_id = args.user_id
    
    # Initialize chatbot
    my_chatbot = Chatbot()
    
    # Override LLM provider if specified
    if args.provider != config.LLM_PROVIDER:
        my_chatbot.responder.provider = args.provider
        if args.provider == "openai":
            my_chatbot.responder._init_openai()
        else:
            my_chatbot.responder._init_gemini()
        logging.info(f"LLM provider overridden to: {args.provider}")
    
    # Set policy token
    success, msg = my_chatbot.set_policy_token(policy_token)
    if not success:
        print(f"Error: {msg}")
        return
    
    # Display welcome message
    print(my_chatbot.get_initial_greeting())
    print(f"\nSession info:")
    print(f"  Role: {args.role}")
    print(f"  Privacy Level: {args.privacy_level}")
    print(f"  Site: {config.SITE_ID}")
    print(f"  LLM Provider: {my_chatbot.responder.provider} ({my_chatbot.responder.model_name})")
    print("\nType 'quit', 'exit', or 'bye' to end the conversation.\n")
    
    try:
        while True:
            user_input = input("You: ")
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("Bot: Take care. Remember, support is always available if you need it.")
                break
            
            if not user_input.strip():
                continue
            
            bot_response = my_chatbot.get_response(user_input)
            print(f"Bot: {bot_response}\n")

    except (KeyboardInterrupt, EOFError):
        print("\nBot: Conversation ended. Stay safe.")
    except Exception as e:
        logging.error(f"Error in main loop: {e}")
        print(f"\nAn error occurred: {e}")

if __name__ == "__main__":
    main()