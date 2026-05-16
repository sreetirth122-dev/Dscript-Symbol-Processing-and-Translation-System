**Dscript Symbol Processing and Translation System**

A graph-based computational framework for processing, analyzing, storing, reconstructing, and translating symbols from the Dscript symbolic writing system.
The project combines computer vision, skeleton analysis, graph traversal, normalization, database construction, and symbolic rendering into a modular software architecture capable of converting Dscript symbols into structured computational representations and translating English text into Dscript symbolic output.

  
**Features**

* Dscript symbol image processing  
* Skletonization and keypoint detection  
* Graph-based stroke extraction  
* Structure-aware normalization  
* JSON-based symbol database  
* Symbol rendering and reconstruction  
* English → Dscript translation system  
* Modular GUI-based application  
* Symbol viewer and database browser  

  
**Project Structure**

project/  
│  
├── app.py                  # Main GUI application  
├── processing.py           # Symbol processing pipeline  
├── translator.py           # Translation rendering module  
├── database.py             # Database management functions  
├── viewer.py               # Symbol viewing/rendering system  
│  
├── data/  
│   └── symbol_database.json  
│  
├── assets/  
│   └── sample_symbols/  
│  
└── README.md  


**Technologies used**

| Category              | Technology   |
| --------------------- | ------------ |
| Programming Language  | Python       |
| GUI Framework         | Tkinter      |
| Image Processing      | OpenCV       |
| Numerical Computation | NumPy        |
| Skeletonization       | scikit-image |
| Graph Processing      | NetworkX     |
| Rendering             | Pillow (PIL) |
| Data Storage          | JSON         |


**Processing Pipeline**

Image Input  
    ↓  
Preprocessing  
    ↓  
Connected Component Extraction  
    ↓  
Skeletonization  
    ↓  
Keypoint Detection  
    ↓  
Stroke Extraction  
    ↓  
Normalization  
    ↓  
Database Storage  
    ↓  
Translation Rendering  


**How It Works**

1. Symbol Input  
Users upload Dscript symbol images and associate them with English alphabet characters.

2. Image Processing  
The system performs:  
* grayscale conversion  
* thresholding  
* noise filtering  
* connected component extraction  
to isolate symbolic structures.  

3. Skeletonization  
Symbols are reduced to one-pixel-wide skeletons while preserving their geometry.

4. Graph-Based Stroke Extraction  
The project uses an edge-based traversal system to:  
* detect strokes  
* preserve loops  
* maintain parallel lines  
* avoid missing structural paths  

5. Symbol Normalization  
A structure-aware normalization system preserves:  
* loops  
* spacing  
* parallel structures  
* symbolic proportions  
while enabling consistent database storage.  

6. Database Construction  
Processed symbols are stored as:  
* stroke coordinates  
* graph structures  
* metadata  
* keypoints  
* spatial relations  
inside a reusable JSON database.  

7. Translation System  
The translator:  
* accepts English sentence input  
* converts letters into Dscript symbols  
* preserves punctuation and spacing
* renders symbolic output visually  


**Running the Project**

Install Dependencies  
* opencv-python  
* numpy  
* pillow   
* networkx  
* scikit-image  

Run the Application  
app.py  


**GUI Modules**

Home Screen  
* Input Symbol  
* View Symbols  
* Translator  

Input Symbol Screen  
* Upload symbol image  
* Process symbol  
* Save mapping to database  
* Preview processed symbol  

Symbol Viewer  
* Displays stored symbols  
* Enlarged symbol preview  
* Processed structure visualization  

Translator  
* English sentence input  
* Dscript symbolic rendering  
* Preserves punctuation and spacing  


**Current Limitations**

* Reverse translation is not fully implemented  
* Symbol mapping is currently manual  
* Sensitive to noisy symbol images  
* Image-based rendering instead of true font generation  
* Complex overlapping structures may affect extraction  


**Future Scope**

* Reverse translation engine  
* Machine learning-based symbol recognition  
* Real-time handwriting recognition  
* Symbol similarity analysis  
* Dscript font generation  
* Real-time translation system  

**Research Focus**

This project explores:  
* symbolic language processing  
* graph-based structural representation  
* computational interpretation of symbolic writing systems  
* translation architectures for non-standard scripts  


**Author**

Sreetirth K K


**License**

This project is intended for academic and research purposes.
