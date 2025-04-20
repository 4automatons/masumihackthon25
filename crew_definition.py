from crewai import Agent, Crew, Task
from logging_config import get_logger
import os
import random
from crewai import Agent, Task, Crew
from crewai.tools import tool

@tool("Sample Filtered Files")
def sample_filtered_files(n: int) -> str:
    """
    Randomly samples N filenames from a file (with one filename per line),
    reads those files from the given directory, and returns their labeled content.
    """
    filtered_list_path =  "./junk_data/junk_data.txt"
    directory = "./data"
    try:
        # Load filtered filenames
        with open(filtered_list_path, "r") as f:
            filenames = [line.strip() for line in f if line.strip()]

        if not filenames:
            return "No filenames found in the filtered list."

        sample_size = min(n, len(filenames))
        sampled_files = random.sample(filenames, sample_size)

        contents = ""
        for fname in sampled_files:
            path = os.path.join(directory, fname)
            if os.path.isfile(path):
                with open(path, "r") as f:
                    contents += f"\n=== {fname} ===\n" + f.read() + "\n"
            else:
                contents += f"\n=== {fname} ===\n[File not found]\n"

        return contents

    except Exception as e:
        return f"Error during sampling from filtered list: {str(e)}"


@tool("Random File Sampler")
def sample_random_files( n: int) -> str:
    """Randomly samples up to N files from a directory and returns their contents."""
    directory = "./data"
    try:
        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        if not files:
            return "No files found."
        sample_size = min(n, len(files))
        sampled_files = random.sample(files, sample_size)
        contents = ""
        for fname in sampled_files:
            path = os.path.join(directory, fname)
            with open(path, "r") as f:
                contents += f"\n=== {fname} ===\n" + f.read() + "\n"
        return contents
    except Exception as e:
        return f"Error during sampling: {str(e)}"
    
@tool("Filter Data and Save")
def filter_data_by_name_and_save(filter_code: str) -> str:
    """
    Filters files in a directory using a custom Python expression on filenames,
    and saves the matching filenames to an output file.

    The filter_code should be a valid Python expression using the variable 'fname',
    e.g., "int(fname.split('.')[0]) % 2 == 0" for even-numbered files.
    """
    directory = "./data"
    output_file = "./junk_data/junk_data.txt"
    try:
        # Ensure output directory exists
        output_path = "output_file"
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        files = [f for f in os.listdir(directory) if os.path.isfile(os.path.join(directory, f))]
        filtered = [f for f in files if eval(filter_code, {}, {"fname": f})]

        if not filtered:
            return "No files matched the filter."

        with open(output_path, "w") as out:
            out.write("\n".join(filtered))

        return f"Saved {len(filtered)} matching filenames to '{output_file}'."

    except Exception as e:
        return f"Error during filtering: {str(e)}"
    

@tool("Filter Data by Content and Save")
def filter_data_by_content_and_save(filter_code: str) -> str:
    """
    Filters files in a directory using a custom Python expression on file contents,
    and saves the matching filenames to an output file.

    The filter_code should be a valid Python expression using the variable 'content',
    e.g., "'ERROR' in content" or "len(content.split()) > 100".
    """
    directory = "./data"
    output_file = "./junk_data/junk_data.txt"

    try:
        # Ensure output directory exists
        output_path = output_file
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        filtered = []
        for fname in os.listdir(directory):
            path = os.path.join(directory, fname)
            if not os.path.isfile(path):
                continue
            with open(path, "r", errors="ignore") as f:
                content = f.read()
                try:
                    if eval(filter_code, {}, {"content": content}):
                        filtered.append(fname)
                except Exception as e:
                    return f"Error evaluating filter on {fname}: {str(e)}"

        if not filtered:
            return "No files matched the content filter."

        with open(output_path, "w") as out:
            out.write("\n".join(filtered))

        return f"Saved {len(filtered)} content-matching filenames to '{output_file}'."

    except Exception as e:
        return f"Error during content filtering: {str(e)}"
    
@tool("Get Confidence Score")
def get_confidence_score(bad: int, total: int) -> str:
    """
    Calculates confidence score from provided bad and total file counts.
    Returns a string: confidence=<score>, bad=<bad>, total=<total>
    """
    if total == 0:
        return "confidence=1.00, bad=0, total=0"

    confidence = bad / total
    return f"confidence={confidence:.2f}, bad={bad}, total={total}"
    
class HypothesisCrew:
    def __init__(self, verbose=True, logger=None):
        self.verbose = verbose
        self.logger = logger or get_logger(__name__)
        self.crew = self.create_crew()
        self.logger.info("ResearchCrew initialized")

    def create_crew(self):
        self.logger.info("Creating research crew with agents")
        

        sampler = Agent(
            role="Data Sampler",
            goal="Randomly sample files and extract their contents for analysis.",
            backstory="You retrieve representative examples from a large LLM dataset to help detect potential issues.",
            tools=[sample_random_files],
            verbose=self.verbose        
        )

        pattern_recognizer = Agent(
            role="Bad Data Detector",
            goal="Identify patterns or anomalies that indicate bad or poisoned data in LLM datasets.",
            backstory=(
                "You are a data forensics expert who specializes in recognizing signs of tampering, hallucination, "
                "unnatural repetition, misleading formatting, or nonsensical responses in LLM data."
            ),
            verbose=self.verbose
        )

        hypothesis_generator = Agent(
            role="Hypothesis Generator for Data Poisoning",
            goal="Generate simple hypotheses for general trends in the data that bad data might follow using general laws with the file names. An example is all bad data is on even file names, or the file names for bad data is divisible by 5.",
            backstory=(
                "You propose intelligent theories about trends within the data on how certain data might be corrupt, biased, or harmful to train on. "
                "Your hypotheses guide future dataset cleaning and auditing processes."
            ),
            verbose=True
        )

        hypothesis_critic = Agent(
            role="Hypothesis Criticizer",
            goal="Critically evaluate hypotheses about poisoned or corrupted data to ensure they are testable, specific, and logically sound.",
            backstory=(
                "You are an expert in experimental methodology and adversarial data analysis. "
                "Your job is to refine or reject hypotheses that are vague or unsupported by the data. "
                "You make sure each hypothesis can be tested using file metadata or content."
            ),
            verbose=self.verbose
        )


        self.logger.info("Created research and writer agents")

        hypothesis_crew = Crew(
            agents=[sampler, pattern_recognizer, hypothesis_generator, hypothesis_critic],
            tasks=[
                Task(
                    description="Sample up to 5 files from the folder './data' and return their contents.",
                    expected_output="A dump of file contents from up to 5 random files.",
                    agent=sampler
                ),
                Task(
                    description="Analyze the sampled data and identify repeated patterns or anomalies.",
                    expected_output="A summary of patterns, rules, or oddities in the data.",
                    agent=pattern_recognizer
                ),
                Task(
                    description="Based on the pattern analysis, generate the most likely hypotheses about the file structure or content anomalies. The hypothesis must select a subset of the file system that has bad data AND ONLY BAD DATA. Examples of hypothesis include all even files are bad. Another example is only file 3 is bad.",
                    expected_output="Three clear hypotheses that could explain trends or issues in the data.",
                    agent=hypothesis_generator
                ),

                Task(
                    description=(
                        "Evaluate the following hypotheses for clarity, testability, and specificity. "
                        "Revise unclear hypotheses and remove any that can't be verified with file structure or content. "
                        "Output a cleaned list of 1 to 3 strong hypotheses with rationale for changes made."
                    ),
                    expected_output="A refined list of one improved hypotheses, with a brief justification.",
                    agent=hypothesis_critic
                ),

            ]
        )

        self.logger.info("Crew setup completed")
        return hypothesis_crew
    

class ScriptCrew:
    def __init__(self, hypothesis_result: str, verbose=True, logger=None):
        self.verbose = verbose
        self.logger = logger or get_logger(__name__)
        self.hypothesis = hypothesis_result
        self.crew = self.create_crew()
        self.logger.info("ResearchCrew initialized")



    def create_crew(self):
        self.logger.info("Creating research crew with agents")
        

        script_writer = Agent(
            role="Script Generator",
            goal=f"Write a script to filter data based on the most likely hypothesis. The hypotheses are: {self.hypothesis}. Your output must be a script. In case you cannot generate a working script just default to even numbers.",
            backstory="You create Python scripts that filter files that must fulfill the hypothesis.",
            verbose=self.verbose
        )

        script_criticizer = Agent(
            role="Script Criticizer",
            goal=f"Make sure the script generated by Script Generator fulfills the hypothesis. The hypotheses are: {self.hypothesis}.  In case you cannot generate a working script just default to even numbers.",
            backstory="You are an agent that criticizes the Script Generator constructively until it generates a good script that fulfills the hypothesis, then you verify it for filter executor.",
            verbose=self.verbose
        )

        filter_executor = Agent(
            role="Filter Executor",
            goal="Apply a filename filter or a file content filter and save matching file contents to a file, only after script criticizer verifies the script.",
            backstory="You take a filter expression and use it to extract relevant data from a directory.",
            tools=[filter_data_by_name_and_save, filter_data_by_content_and_save],  
            verbose=self.verbose
        )


        script_crew = Crew(
            agents=[script_writer, script_criticizer, filter_executor],
            tasks=[
                Task(
                    description="Generate a Python expression that finds bad files matching the most likely hypothesis. "
                                "For example, if the hypothesis says even-numbered files are bad, the expression might be: "
                                "'int(fname.split(\".\")[0]) % 2 == 0'",
                    expected_output="A safe Python expression using 'fname' that returns True for matching files and that is sufficiently simple that it runs without errors.",
                    agent=script_writer
                ),

                Task(
                    description="Criticize a Python expression that finds bad files matching the hypothesis. "
                                "For example, if the hypothesis says even-numbered files are bad, the expression might be: "
                                "'int(fname.split(\".\")[0]) % 2 == 0', Check if it really does fulfill the hypothesis and is good code.",
                    expected_output="Constructive criticism that prompts Script Generator to make better scripts.",
                    agent=script_criticizer
                ),

                Task(
                    description="Use the generated script to find bad data files from './data' and save their names to './junk_data/' as the file junk_data.txt.",
                    expected_output="A confirmation message that filtered data was saved.",
                    agent=filter_executor
                ),         

            ]
        )

        self.logger.info("Crew setup completed")
        return script_crew
    

class ResearchCrew:
    def __init__(self, script_result : str, verbose=True, logger=None):
        self.verbose = verbose
        self.logger = logger or get_logger(__name__)
        self.script = script_result
        self.crew = self.create_crew()
        self.logger.info("ResearchCrew initialized")

    def create_crew(self):
        self.logger.info("Creating research crew with agents")
        

        filtered_sampler = Agent(
            role="Filtered Sampler",
            goal=f"Sample randomly from the filtered dataset for evaluation. Using the script generated by the previous agents. The previous agent response is: {self.script}",
            backstory="You provide representative examples from the filtered data for testing hypotheses.",
            tools=[sample_filtered_files],
            verbose=self.verbose
        )


        confidence_tester = Agent(
            role="Confidence Tester",
            goal="Evaluate the quality of the hypothesis based on the proportion of bad data files to total data files in the subset.",
            backstory="You evaluate how valid a hypothesis is by checking how much bad data is in the selected files.",
            tools=[get_confidence_score],
            verbose=True
        )

        lab_manager = Agent(
            role="Lab Manager",
            goal="Go over everybody's work. Make them repeat work if they don't work properly.",
            backstory="You are a world renowned researcher famous for good experiments. Your job is to guide your crew to finding bad data.",
            verbose=self.verbose
        )



        research_crew = Crew(
            agents=[filtered_sampler, confidence_tester, lab_manager],
            tasks=[
                Task(
                    description="Sample data based on the hypothesis-generated filter (e.g., even-numbered files) and return the sampled content.",
                    expected_output="The sampled content from files that match the hypothesis filter.",
                    agent=filtered_sampler
                ),

                Task(
                    description="Use the sampled data to test the hypothesis and return a confidence score based on bad data detection.",
                    expected_output="Confidence score based on the ratio of bad data in the sampled files.",
                    agent=confidence_tester
                ),

                Task(
                    description="Manages the research crew into giving good hypotheses that sufficiently capture all the bad data.",
                    expected_output="'We have found bad data accurately' or 'Our hypothesis was disproven' based on high confidence and low confidence respectively. Also, please state confidence scores using the tool you are given.",
                    agent=lab_manager
                ),


            ]
        )

        self.logger.info("Crew setup completed")
        return research_crew