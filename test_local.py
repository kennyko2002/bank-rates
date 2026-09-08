import os
os.environ["MONGODB_URI"] = "mongodb+srv://kenny:Qwer1234@cluster0.6abxj.mongodb.net/cbc_rate?retryWrites=true&w=majority"

# Now import and run the app
import uvicorn
from api.rates import app

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8765)