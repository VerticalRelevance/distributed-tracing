import boto3

def create_inference_profile():
    # Initialize the Bedrock client
    bedrock_client = boto3.client('bedrock', region_name='us-west-2')
    
    # Define the profile configuration
    profile_config = {
        "name": "example-inference-profile",
        "description": "Inference profile for Claude 3.5",
        "modelIds": ["anthropic.claude-3-5-sonnet-20241022-v2:0"],
        "parameters": {
            "default": {
                "temperature": 0.7,
                "max_tokens_to_sample": 200
            }
        }
    }

    try:
        # Create the inference profile
        response = bedrock_client.create_inference_profile(**profile_config)
        print("Inference Profile Created:")
        print(f"Name: {response['name']}")
        print(f"ARN: {response['inferenceProfileArn']}")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    create_inference_profile()
