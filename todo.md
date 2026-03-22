# Project Plan: BM25 vs. SBERT for Lecture Slide Retrieval

## Done so far

Set up the project structure and dependencies. Configured the project with a central config file for paths, chunking parameters, retrieval settings, and model choices. Probably needs to be udpated. Collected the initial set of TDT4310 lecture PDFs and got them into a consistent naming scheme. I made git not track the PDFs, nor the extracted text files - in case the professor doesnt want them in the repo publically available. 

The PDF extraction pipeline is up and running. I wrote a module that reads each PDF page as a slide, pulls out the text with pdfplumber, cleans away headers/footers/slide numbers, and extracts slide titles. I ran it on the TDT4310 lectures, dumped the raw text to files, and manually verified that the extraction looks clean against the original slides.

## What's left to do

**Question generation:** I've already generated questions for TDT4310, and they're stored in `data/questions.json`, but we should probably make new ones later, maybe using LLama - creating a replicable script for it. I have an idea for format, but it requires implementation of chunking first. The questions are already in that format, but do not contain chunk_id etc. The ones there now were made with Claude.

**Chunking** — Turn the extracted slides into proper retrieval chunks. Each slide becomes a chunk with metadata (course, lecture, slide number, title). Short slides get filtered out(?), long ones get split with some overlap(?). Everything gets saved as a JSONL file for downstream use.

**BM25 retrieval** 

**SBERT retrieval** 

**Run retrieval on all questions** 

**LLM-as-judge relevance labeling** 

**Human proofing** 

**Chunk size ablation** 

**Evaluation** 

**Analysis notebooks** 

**Add more courses(?)** 

**RAG extension(?)** 

**Report** 