import boto3

def list_inference_profiles_for_model(model_id):
    # Create a Bedrock client
    bedrock_client = boto3.client('bedrock', region_name='us-west-2')

    try:
        # List all inference profiles
        response = bedrock_client.list_inference_profiles()
        profiles = response.get('inferenceProfiles', [])
        
        # Filter profiles associated with the specific model
        relevant_profiles = [
            profile for profile in profiles
            if model_id in profile.get('modelIds', [])
        ]

        # Display the relevant profiles
        if relevant_profiles:
            print(f"Inference profiles for model '{model_id}':")
            for profile in relevant_profiles:
                print(f"- Name: {profile['name']}")
                print(f"  ID: {profile['inferenceProfileId']}")
                print(f"  ARN: {profile['inferenceProfileArn']}")
        else:
            print(f"No inference profiles found for model '{model_id}'.")
    
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    # Replace with the model ID of interest
    model_id = "anthropic.claude-3-5-sonnet-20241022-v2:0"
    list_inference_profiles_for_model(model_id)
