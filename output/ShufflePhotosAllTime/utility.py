import botocore.session
from botocore.stub import Stubber
from unittest.mock import patch, Mock, MagicMock


def setup_boto3_mocking(aws_client, method_and_return_array):
		print(f"Stubbing with: {aws_client}")
		# stubbed_client = boto3.client('s3') --- seems like this should work but does not
		stubbed_client = botocore.session.get_session().create_client(aws_client)
		stubber = Stubber(stubbed_client)

		for method in method_and_return_array:
			client_method = method[0]
			fake_return_value = method[1]
			print(f"\tstubbing {client_method} with {fake_return_value}")

			stubber.add_response(client_method, fake_return_value)
		stubber.activate()
		print("Stubber:")
		print(stubber)
		return stubbed_client

