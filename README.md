# toaster-city-lambda

This is the source code for the *toaster-city-inventory* AWS Lambda Function.


## Structure

- **`src/`**: Contains all the source code for the Lambda functions, including the main entry point and routing logic.

- **`src/main.py`**: The main entry point for the Lambda function, implementing the `lambda_handler()` that processes incoming events. It delegates the request to the router for further processing.

- **`src/router.py`**: Responsible for determining which resource the incoming event corresponds to, and routing it to the appropriate handler based on that determination.

- **`src/handlers/`**: Contains handler classes that are collections of relevant endpoints. Each class groups endpoints of a resource (e.g. inventory-management), allowing for shared logic among multiple endpoints.

- **`src/services/`**: Encapsulates the business logic for the application, promoting separation of concerns and making testing and maintenance easier.

- **`src/utils/`**: Contains utility functions and helper methods that can be reused across different modules.

- **`src/test.ipynb`**: A Jupyter Notebook used as a playground for the devs. This notebook is there for devs to test out code snippets, explore new ideas, and validate functionality. The code in the playground notebook is **not important** to the project and should not be relied upon for production use. Developers are allowed to **overwrite or delete** any code in this notebook as needed. It is a temporary space for testing and should not contain any important or critical code. Please ensure that important code is saved in the appropriate source files within the project structure. So any code that you value should not be in there after a commit.


## Environment
To run this project, ensure you have the necessary environment configurations in place.

### Dependencies
The project relies on packages listed in `requirements.txt`. You are welcome to use either a virtual environment or install the packages globally.

### Environment Variables
For the application to connect to the database, you need to set an environment variable named `toast_db_conn_str` with the connection string to the database. 

Please note that the Jupyter Notebook has its own set of environment variables outside of the OS. So environment variables accessible in a regular `.py` file might not be accessible in the Jupyer Notebook.


## Deployment

The project is automatically deployed to AWS Lambda whenever changes are made to the `main` branch of the repository.

The current package requirements for the project are configured as AWS Layers that are attached to the Lambda function on AWS. If any new packages are needed, they should be added to the appropriate layer configuration.

The `pandas` package is managed as a separate layer on AWS (named `AWSSDKPandas-Python312`). This layer is not uploaded by our team because `pandas` has specific requirements, and managing our own version would involve unnecessary complexity. It is more efficient to use the provided AWS layer for this library.

Ensure that any new packages are properly added to the existing layers to maintain the functionality of the Lambda function during deployment.