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
<!-- pytest output -->
```

### B3 — The loop

- Round limit, and why:
- Where the logs are:
- Real Q-09 conversation compared with my A3 version, what is different:

### B4 — Three strategies

**What I kept the same:**

<!-- model, temperature, k, prompts, answer format, anything else -->

**My rule for a correct answer** (written before the first full run):

| Run | Strategy | Correct /20 | Unanswered | Input tokens | Output tokens | Median seconds per question | Total seconds | Cost ($) |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| 1 | S1 direct | | | | | | | |
| 1 | S2 think and vote (k = ) | | | | | | | |
| 1 | S3 tools | | | | | | | |
| 2 | S1 direct | | | | | | | |
| 2 | S2 think and vote (k = ) | | | | | | | |
| 2 | S3 tools | | | | | | | |

**Per question (run 1):**

| Question | S1 | S2 | S3 |
|---|:---:|:---:|:---:|
| Q-01 | | | |
| Q-02 | | | |
| Q-03 | | | |
| Q-04 | | | |
| Q-05 | | | |
| Q-06 | | | |
| Q-07 | | | |
| Q-08 | | | |
| Q-09 | | | |
| Q-10 | | | |
| Q-11 | | | |
| Q-12 | | | |
| Q-13 | | | |
| Q-14 | | | |
| Q-15 | | | |
| Q-16 | | | |
| Q-17 | | | |
| Q-18 | | | |
| Q-19 | | | |
| Q-20 | | | |

---

## Part C — Explain and choose (Hard)

### C1 — Does the tool description matter?

| Question | Calls (your description) | Calls (vague) | Answer (yours) | Answer (vague) |
|---|---:|---:|---|---|
| | | | | |

### C2 — Three mistakes explained

### C3 — Which strategy I would use, and what would change it

### C4 — How sure I can be

### Final questions

1.
2.
3.
4.
5.
6.
7.
8.
