# About
A useful but simple chatbot utilizing Anthropic Claude models on AWS Bedrock.

This app was developed entirely using Anthropic Claude 3.5 Sonnet. It began with a simple prompt: 
> let's develop a python streamlit app that uses boto3 to utilze aws bedrock models.

Currently, three of the leading Anthropic models are included as options the user can choose:
- Claude 3.5 Sonnet
  - Claude 3.5 Sonnet is comparable to ChatGPT 4o.
- Claude 3 Haiku
- Claude Instant

The other Anthropic models are easy to include. Simply add them as options in main.py. 

Select [this link](https://aws.amazon.com/bedrock/claude) to learn more about the Anthropic models on Bedrock.

# Settings - options
While running the app, you can do the following:
- Change the selected model
- Set custom model paramters:
    - Temperature
    - Top K
- Select a system prompt from simple pre-supplied prompts.
    - System Prompts are separate from the user prompt. They are used to instruct the model how to behave and they are included in each request a user makes.
    - Example system prompt:
    - > Respond to my requests and questions like a kind school teacher.
- Create and use a **Custom system prompt** to test out various prompt techniques to tailor the bot for your use.
- Clear chat history.

# Running the app
A Dockerfile is included for reference on how to build the image to run in Docker or to deploy as a container.

Otherwise, a simple start and stop script are also included to run the app, assuming python and the required python libaries have been installed. Reference the Dockerfile for guidance here too.

# Authentication
The app is intended to run with AWS credentials with an AWS account that has access to bedrock. You will need an IAM user or role with access to the becrock models to run the app.

For example, you can set the environment variables where the app is running:
```
export AWS_ACCESS_KEY_ID=your_access_key
export AWS_SECRET_ACCESS_KEY=your_secret_key
```

Or add these values directly to the boto3 client in main.py

```
AWS_ACCESS_KEY_ID = "your_access_key_id"
AWS_SECRET_ACCESS_KEY = "your_secret_access_key"
AWS_REGION = "us-east-1"  # or your preferred region

bedrock = boto3.client(
    service_name='bedrock-runtime',
    region_name=AWS_REGION,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY
)
```

# How Bedrock models are called (libraries)
The app simply uses boto3 bedrock-runtime and the Converse API. 
```
import boto3
bedrock = boto3.client( service_name='bedrock-runtime' )
response = bedrock.converse()

```
You could instead use LangChain, for example.
```
from langchain_aws import ChatBedrockConverse
```