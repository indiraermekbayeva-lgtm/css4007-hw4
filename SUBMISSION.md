# HW4 — submission

**AI assistance:** <!-- what you used, and for what. "None" is an answer too. -->

---

## Part A — Plan on paper (Easy)

> Commit this whole part before any `.py` file exists.

### A1 — The steps

| # | Step | What goes in (types) | What comes out (types) | When it goes wrong | Tool, loop, or model? |
|---|---|---|---|---|---|
| 1 | Understand the question | question (str) | districts and fields (list[str]) | Report unclear question | Model |
| 2 | Find data | district (str), field (str) | value (float), unit (str), source (str) | Report missing or ambiguous data | lookup tool |
| 3 | Check data | retrieved facts (dict) | valid facts (dict) | Ignore archived data, apply corrections, report unknown units | lookup tool |
| 4 | Prepare calculation | valid facts (dict) | expression (str) | Report missing values | Model |
| 5 | Calculate | expression (str) | result (float) | Return error for invalid expressions or division by zero | calculate tool |
| 6 | Compare | results (list[float]) | name (str), difference (float) | Report if comparison fails | Model |
| 7 | Give final answer | name (str), difference (float) | answer (str) | Mark unanswered if data is insufficient | Model |


**How the steps connect:**

Question → Understand → Lookup → Check data → Prepare calculation → Calculate → Compare → Final answer

**What I am assuming:**

I use valid data for 2025 and ignore archived profiles. I apply correction notices before calculations. I convert units when needed and round only the final result. If information is missing or unclear, I return an error instead of guessing.

### A2 — The two tools

#### `lookup`

```json
{
  "type": "function",
  "function": {
    "name": "lookup",
    "description": "Find a specific fact about a district in the documents. Use valid 2025 data, ignore archived profiles, apply corrections, and return the source document ID.",
    "parameters": {
      "type": "object",
      "properties": {
        "district": {
          "type": "string",
          "description": "District name"
        },
        "field": {
          "type": "string",
          "description": "Information to find, such as population or area"
        }
      },
      "required": ["district", "field"],
      "additionalProperties": false
    }
  }
}
```

| Case | What the tool returns |
|---|---|
| Success | Value, unit, and source document ID |
| District not found | Error message with suggested district names |
| Similar district names | Exact match or an ambiguity error |
| Archived profile | Ignore old data and use the valid profile |
| Corrected value | Return the corrected value and correction source |
| Unknown field | Error explaining that the field is unavailable |
| Invalid input | Error message without crashing |

**Worst thing it could do with strange or dangerous input:**

The lookup tool could return incorrect information, confuse similar district names, or expose too much document text. I will validate inputs, limit the returned text, and handle errors safely.

#### `calculate`

```json
{
  "type": "function",
  "function": {
    "name": "calculate",
    "description": "Safely calculate an arithmetic expression using numbers and basic mathematical operators.",
    "parameters": {
      "type": "object",
      "properties": {
        "expression": {
          "type": "string",
          "description": "Arithmetic expression, such as 15000 - 10000 or 44675 / 921.4"
        }
      },
      "required": ["expression"],
      "additionalProperties": false
    }
  }
}
```

| Case | What the tool returns |
|---|---|
| Success | Calculated numeric result |
| Division by zero | Error: division by zero |
| Invalid expression | Error: unsupported expression |
| Dangerous code | Error: only arithmetic is allowed |
| Very large numbers | Error: calculation limit exceeded |
| Empty input | Error: expression is required |

**Worst thing it could do with strange or dangerous input:**

The calculate tool could receive dangerous Python code or very large expressions. I will use the ast module instead of eval or exec, allow only basic arithmetic operators, and limit expression size to prevent unsafe execution.

### A3 — Q-09 by hand

```json
[
  {
    "role": "user",
    "content": "Which district has the higher population density in 2025, Brightwater or Millbrook, and by how many residents per square kilometre?"
  },
  {
    "role": "assistant",
    "tool_calls": [
      {
        "id": "call_1",
        "type": "function",
        "function": {
          "name": "lookup",
          "arguments": "{\"district\":\"Brightwater\",\"field\":\"population\"}"
        }
      },
      {
        "id": "call_2",
        "type": "function",
        "function": {
          "name": "lookup",
          "arguments": "{\"district\":\"Brightwater\",\"field\":\"area\"}"
        }
      },
      {
        "id": "call_3",
        "type": "function",
        "function": {
          "name": "lookup",
          "arguments": "{\"district\":\"Millbrook\",\"field\":\"population\"}"
        }
      },
      {
        "id": "call_4",
        "type": "function",
        "function": {
          "name": "lookup",
          "arguments": "{\"district\":\"Millbrook\",\"field\":\"area\"}"
        }
      }
    ]
  },
  {
    "role": "tool",
    "tool_call_id": "call_1",
    "content": "{\"value\":44675,\"unit\":\"residents\",\"source\":\"NR-05\"}"
  },
  {
    "role": "tool",
    "tool_call_id": "call_2",
    "content": "{\"value\":921.4,\"unit\":\"km2\",\"source\":\"NR-16\",\"note\":\"Corrected area; NR-05 contains a typo\"}"
  },
  {
    "role": "tool",
    "tool_call_id": "call_3",
    "content": "{\"value\":37203,\"unit\":\"residents\",\"source\":\"NR-11\"}"
  },
  {
    "role": "tool",
    "tool_call_id": "call_4",
    "content": "{\"value\":758.6,\"unit\":\"km2\",\"source\":\"NR-11\"}"
  },
  {
    "role": "assistant",
    "tool_calls": [
      {
        "id": "call_5",
        "type": "function",
        "function": {
          "name": "calculate",
          "arguments": "{\"expression\":\"44675 / 921.4\"}"
        }
      },
      {
        "id": "call_6",
        "type": "function",
        "function": {
          "name": "calculate",
          "arguments": "{\"expression\":\"37203 / 758.6\"}"
        }
      }
    ]
  },
  {
    "role": "tool",
    "tool_call_id": "call_5",
    "content": "{\"result\":48.48599956587801}"
  },
  {
    "role": "tool",
    "tool_call_id": "call_6",
    "content": "{\"result\":49.041655681518584}"
  },
  {
    "role": "assistant",
    "tool_calls": [
      {
        "id": "call_7",
        "type": "function",
        "function": {
          "name": "calculate",
          "arguments": "{\"expression\":\"49.041655681518584 - 48.48599956587801\"}"
        }
      }
    ]
  },
  {
    "role": "tool",
    "tool_call_id": "call_7",
    "content": "{\"result\":0.5556561156405735}"
  },
  {
    "role": "assistant",
    "content": "Millbrook has a higher population density by 0.6 residents per km2.\nANSWER: Millbrook | 0.6"
  }
]
```

**My arithmetic:**

Brightwater population (2025): 44675 (NR-05)
Brightwater corrected area: 921.4 km2 (NR-16)
Millbrook population (2025): 37203 (NR-11)
Millbrook area: 758.6 km2 (NR-11)

Brightwater density = 44675 / 921.4 = 48.48599956587801
Millbrook density = 37203 / 758.6 = 49.041655681518584
Difference = 49.041655681518584 - 48.48599956587801 = 0.5556561156405735

Rounded to 1 decimal place: 0.6

Final answer: Millbrook has a higher population density by 0.6 residents per km2.

### A4 — Why I split it this way

An alternative approach is to create one large tool that finds information and performs calculations together.

I did not choose this approach because it is harder to test and find errors. I decided to use two separate tools: `lookup` for finding information and `calculate` for arithmetic.

This approach is easier to understand, test, and maintain. It also helps me identify whether a mistake comes from incorrect data or a calculation.

---

## Part B — Build it and run it (Medium)

### What I changed from Part A while coding

<!-- what changed in your plan, and why. "None" is an answer too. -->

### B2 — Tests

```text
30 passed in 0.05s
```

### B3 — The loop

- Round limit, and why: 12 rounds. This prevents the model from calling tools forever.
- Where the logs are: The logs are saved in the `outputs/` folder. The S3 results are in `outputs/S3_results.jsonl`.
- Real Q-09 conversation compared with my A3 version, what is different:

  In A3, I planned 4 lookup calls and 3 calculate calls.

  In the real run, the model used 4 lookup calls and only 2 calculate calls.

  The real conversation took 3 rounds:
  - Round 1: The model looked up population and area for both districts.
  - Round 2: The model calculated both population densities.
  - Round 3: The model returned the final answer.

  The model used the corrected Brightwater area of 921.4 km2 from NR-16.

  The main difference is that the real model calculated the final difference itself, without a third calculate tool call.

  Both versions gave the same answer: Millbrook, 0.6 residents per km2.
  
### B4 — Three strategies

**What I kept the same:**

I used the same model, `gpt-5.6-luna`, for all three strategies.

I used the same 20 questions and repeated each strategy twice.

I used the same system instructions and JSON answer format.

S1 answered each question directly using the full corpus.
S2 generated 5 independent answers and used majority voting (k = 5).
S3 used the lookup and calculate tools.

For S3, I set reasoning_effort to "none" because the API did not support function tools with the previous reasoning setting.

**My rule for a correct answer** (written before the first full run):

An answer is correct only if both the district name and the numerical value match the gold answer. The numerical value is compared after rounding to the required number of decimal places. Missing or invalid answers are incorrect.

| Run | Strategy | Correct /20 | Unanswered | Input tokens | Output tokens | Median seconds per question | Total seconds | Cost ($) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | S1 direct | 20 | 0 | 44760 | 11277 | 5.06 | 117.64 | 0.02248 |
| 1 | S2 think and vote (k = 5) | 17 | 1 | 223800 | 54611 | 26.64 | 483.02 | 0.11029 |
| 1 | S3 tools | 17 | 0 | 41576 | 4932 | 4.04 | 84.71 | 0.01423 |
| 2 | S1 direct | 19 | 0 | 44760 | 11244 | 5.05 | 107.76 | 0.02244 |
| 2 | S2 think and vote (k = 5) | 20 | 0 | 223800 | 54787 | 23.91 | 482.39 | 0.11050 |
| 2 | S3 tools | 17 | 0 | 41045 | 4818 | 3.80 | 80.27 | 0.01399 |

**Per question (run 1):**

| Question | S1 | S2 | S3 |
|---|:---:|:---:|:---:|
| Q-01 | ✓ | ✓ | ✓ |
| Q-02 | ✓ | ✓ | ✓ |
| Q-03 | ✓ | ✓ | ✓ |
| Q-04 | ✓ | ✓ | ✗ |
| Q-05 | ✓ | ✗ | ✓ |
| Q-06 | ✓ | ✓ | ✓ |
| Q-07 | ✓ | ✓ | ✓ |
| Q-08 | ✓ | ✗ | ✗ |
| Q-09 | ✓ | ✓ | ✓ |
| Q-10 | ✓ | ✓ | ✓ |
| Q-11 | ✓ | ✓ | ✓ |
| Q-12 | ✓ | ✓ | ✓ |
| Q-13 | ✓ | ✓ | ✓ |
| Q-14 | ✓ | ✓ | ✓ |
| Q-15 | ✓ | ✓ | ✓ |
| Q-16 | ✓ | ✓ | ✓ |
| Q-17 | ✓ | ✓ | ✗ |
| Q-18 | ✓ | ✗ | ✓ |
| Q-19 | ✓ | ✓ | ✓ |
| Q-20 | ✓ | ✓ | ✓ |

**Per question (run 2):**

| Question | S1 | S2 | S3 |
|---|:---:|:---:|:---:|
| Q-01 | ✓ | ✓ | ✓ |
| Q-02 | ✓ | ✓ | ✓ |
| Q-03 | ✓ | ✓ | ✓ |
| Q-04 | ✓ | ✓ | ✓ |
| Q-05 | ✓ | ✓ | ✓ |
| Q-06 | ✓ | ✓ | ✓ |
| Q-07 | ✓ | ✓ | ✓ |
| Q-08 | ✗ | ✓ | ✗ |
| Q-09 | ✓ | ✓ | ✓ |
| Q-10 | ✓ | ✓ | ✓ |
| Q-11 | ✓ | ✓ | ✗ |
| Q-12 | ✓ | ✓ | ✓ |
| Q-13 | ✓ | ✓ | ✓ |
| Q-14 | ✓ | ✓ | ✓ |
| Q-15 | ✓ | ✓ | ✓ |
| Q-16 | ✓ | ✓ | ✓ |
| Q-17 | ✓ | ✓ | ✗ |
| Q-18 | ✓ | ✓ | ✓ |
| Q-19 | ✓ | ✓ | ✓ |
| Q-20 | ✓ | ✓ | ✓ |

---

## Part C — Explain and choose (Hard)

### C1 — Does the tool description matter?

| **Question** | **Calls (your description)** | **Calls (vague)** | **Answer (yours)** | **Answer (vague)** |
| ------------ | ----------------------------: | ----------------: | ------------------ | ------------------ |
| Q-01 | 7 | 9 | Ossbridge, 4.57 | Ossford, no value |
| Q-04 | 7 | 6 | yes, 2.59 | no, 0 |
| Q-08 | 7 | 6 | yes, 1.22 | no, 0 |
| Q-09 | 6 | 9 | Millbrook, 0.56 | Millbrook, 0.56 |
| Q-17 | 7 | 8 | Harrowfield, 75075.28 | no, 0 |
| **Total** | **34** | **38** | | |

The normal description produced no tool errors in these five questions.
The vague description produced 28 tool errors.

For example, in Q-01, the model requested "2025 population"
instead of the valid field "population". The tool returned
"Field not found".

The vague description caused more tool errors and incorrect answers.
Q-09 remained correct, but the model needed more tool calls.
This shows that clear tool descriptions help the model use tools correctly.

### C2 — Three mistakes explained

**S1 — Q-20 (slowest question)**

S1 answered all questions correctly in run 1, so I chose its
slowest question, Q-20.
The model compared the budget per resident of three districts.
It answered Ashgrove with a difference of 2993.342836 tenge.
The answer was correct after rounding, but it took 17.653 seconds
and used 3376 tokens.
The question took longer because it required several comparisons
and calculations.

```text
Answer: Ashgrove
Value: 2993.342836
Time: 17.653 seconds
Total tokens: 3376
```

**S2 — Q-05 (voting failure)**

The correct answer was Coldharbour, 14235 tenge per resident,
but S2 returned 4235.314.
The five trials gave different values: 4235.314, 14235.314487,
14235.314486, 4235.31, and 14235.314486.
Because the voting system treated these as different answers,
each received one vote. It selected the first, incorrect value.
This shows that voting does not always fix mistakes.

```text
Trial 1: Coldharbour, 4235.314
Trial 2: Stonecairn, 14235.314487
Trial 3: Coldharbour, 14235.3144864028
Trial 4: Coldharbour, 4235.31
Trial 5: Coldharbour, 14235.314486389

Final answer: Coldharbour, 4235.314
Correct answer: Coldharbour, 14235
```

**S3 — Q-17 (wrong formula)**

The correct answer was Harrowfield, 884 tenge per resident,
but S3 returned 75075.28.
The model looked up budget, water, and population data, then
used budget values instead of the water tariff. The calculator
evaluated the formula correctly, but the formula was wrong.
This shows that a calculator cannot fix incorrect data selection
or a wrong formula.
S3 needed several rounds to retrieve data, calculate, and answer.
Later rounds include earlier messages and tool results, so input
tokens can increase. More rounds can mean more time and cost.

```text
Correct answer: Harrowfield, 884
Model answer: Harrowfield, 75075.28163049794

Calculator expression:
16021.7*1000000/(7146*1000000/90212)
- 9284.5*1000000/(3862*1000000/52904)
```

The calculator evaluated the expression, but the model
selected the wrong values for the calculation.

### C3 — Which strategy I would use, and what would change it

I would choose S1 (direct) for this task because it had the
highest accuracy and reasonable running time.

| Strategy | Accuracy (2 runs) | Avg. tokens per run | Avg. time per run |
|---|---:|---:|---:|
| S1 | 97.5% (39/40) | 56,021 | 112.7 s |
| S2 | 92.5% (37/40) | 278,499 | 482.7 s |
| S3 | 85% (34/40) | 46,186 | 82.5 s |

S1 was the most accurate strategy.
S2 used almost five times more tokens than S1 and was much slower.
S3 was the fastest and used the fewest tokens, but it made
more mistakes.

I would not choose S2 as my default because voting did not
always fix mistakes. I would not choose S3 as my default
because it sometimes selected the wrong data or formula.

My choice would change in these situations:

1. **Very limited time:** I would choose S3 because it was fastest.

2. **A much larger corpus:** I would consider S3 because it can
   retrieve relevant facts instead of including the entire corpus
   in every prompt. I would test its accuracy first.

3. **A very small token budget:** I would consider S3 because
   it used the fewest tokens, but I would check its answers
   carefully.

The best strategy depends on accuracy, time, token usage,
and the type of task.

### C4 — How sure I can be

The results were different between the two runs.

S1 scored 20/20 in run 1 and 19/20 in run 2.
S2 scored 17/20 in run 1 and 20/20 in run 2.
S3 scored 17/20 in both runs.

S1 changed by 1 correct answer (5 percentage points).
S2 changed by 3 correct answers (15 percentage points).
S3 had the same accuracy in both runs, but some individual
answers were different.

Across both runs, S1 achieved 97.5% accuracy, S2 achieved
92.5%, and S3 achieved 85%.

The difference between the two best strategies, S1 and S2,
was only 5 percentage points. This was smaller than S2's
15-percentage-point change between runs.

Therefore, I cannot be completely sure that S1 is always
better than S2. The results suggest that S1 is a good choice,
but two runs with 20 questions are not enough for a strong
conclusion.

I would test at least 100 different questions per strategy
and repeat the experiments several times. This would help
me understand whether the differences are consistent.

### Final questions

1. The model has only requested a tool call. The tool has not executed yet. My Python program must execute the requested function and send its result back to the model.
2. The API returns tool arguments as a JSON string. I use `json.loads()` to convert the string into a Python dictionary and pass the values to the function. Passing the raw string directly can cause an error because the function expects named arguments.
3. I measured the two tool definitions using `tiktoken` with the `o200k_base` encoding. Together, they contain approximately 209 tokens. This is an estimate of the tool definitions' token count, not the exact API billing overhead.
4. Across both runs, S1 cost approximately $0.04492, while S2 cost $0.22079. S2 cost $0.17587 more, which is about 4.92 times the cost of S1. This happened because S2 made five model calls per question instead of one, using many more input and output tokens.
5. Q-11 in run 1 needed the most rounds: 6. The model first used `lookup` to get the number of pupils and schools for Redfen, Ashgrove, and Millbrook. Then it used `calculate` in four separate rounds to compare pupils per school and find the difference. In the sixth round, it returned the final answer: Redfen, 56.1 pupils per school.
6. If there were 100,000 documents, I would add a search index to make `lookup` faster. The tool would search by district, year, and field instead of checking every document. It would return only the relevant information with source IDs, so the model would not receive unnecessary data.
7. My `calculate` tool uses Python's `ast` parser instead of `eval()` and only allows basic mathematical operations. This prevents the model from running arbitrary Python code. However, the model can still provide a wrong formula or incorrect values, as happened in Q-17. The calculator can calculate correctly, but the final answer can still be wrong.
8. Tools helped most with questions that required looking up several facts and doing calculations. For example, S3 answered Q-05 correctly in both runs, while S2 made a mistake in run 1. However, tools did not improve simple factual questions like Q-10, because all three strategies answered it correctly. Tools also could not prevent mistakes when the model selected the wrong formula, as happened in Q-17.
