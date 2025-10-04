🧠 TextMorph
Project Overview
TextMorph is an advanced text processing application designed for summarization and paraphrasing, built as part of a milestone-driven development internship project. ✅ The project has successfully completed all planned milestones, encompassing:

    *🧪 Model training

    *🔗 Backend and frontend integration

    *📊 Evaluation systems

    *🛠️ Admin dashboard for content and user management

📦 Model Checkpoints:
The necessary pre-trained models for summarization and paraphrasing have been uploaded to Google Drive due to their large size (~2.08 GB each). 📥 Please download the models from the following link: 
    *facebook-bart-summary :- https://drive.google.com/drive/folders/17vlFTM0ZSE_DQ3YGDT8NNck1UiAe-2Ay?usp=drive_link
    *facebook-bart-paraphrase :- https://drive.google.com/drive/folders/1fLjidgeBNmuxMcXKhwshfsQlALGeYsW-?usp=drive_link
    *pegasus-xsum :- https://drive.google.com/drive/folders/1DU8I2ORp4J42CaA4ffXaSFY918ht0Vo4?usp=drive_link

📁 After downloading, place the model files inside the project directory at:

backend/models/

📚 Dataset:
The dataset used for training and evaluation is also available for download via Google Drive: 
    *dataset: https://drive.google.com/file/d/1IOxJszNGT6B6ZJFatdH_ixEamusSTuOJ/view?usp=drive_link

If you are going to use your own dataset make sure that it has input_text, target_text and task(summary or paraphrase) columns.
📁 Download the dataset and place it in the project directory under:

dataset/

⚙️ Setup Instructions:
📝 Create a .env file in the project root containing your environment variables—refer to .env.example for required variable names.

📦 Install project dependencies using pip:
pip install -r requirements.txt
✅ Ensure that the downloaded model checkpoints and dataset are in the paths specified above.

🚀 Run the application.