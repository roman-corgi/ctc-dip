#!/bin/bash
SCHEMA_FILE=$1
XML_FILE=$2

# Step 1: Structural XSD Check
if ! xmllint --noout --schema "$SCHEMA_FILE" "$XML_FILE"; then
    echo "❌ XSD Structural Validation Failed."
    exit 1
fi

# Step 2: Query blocks using the type attribute directly
XPATH_QUERY="//*[@type='rpn']"
BLOCK_COUNT=$(xmllint --xpath "count($XPATH_QUERY)" "$SCHEMA_FILE" 2>/dev/null)
BLOCK_COUNT=${BLOCK_COUNT:-0}

if [ "$BLOCK_COUNT" -eq 0 ]; then
    echo "⚠ Warning: No elements with type='rpn' found."
    exit 0
fi

declare -i PIPELINE_FAILED=0

# Step 3: Loop and Analyze Balance using direct tag names
for (( i=1; i<=$BLOCK_COUNT; i++ )); do
    TAG_NAME=$(xmllint --xpath "string(($XPATH_QUERY)[$i]/@name)" "$SCHEMA_FILE" 2>/dev/null)
    
    # Clean, direct tag selection without local-name() syntax overhead
    OPERANDS=$(xmllint --xpath "count(/*/*[local-name()='$TAG_NAME']//*[local-name()='operand'])" "$XML_FILE" 2>/dev/null)
    OPERATORS=$(xmllint --xpath "count(/*/*[local-name()='$TAG_NAME']//*[local-name()='operator'])" "$XML_FILE" 2>/dev/null)
    
    OPERANDS=${OPERANDS:-0}
    OPERATORS=${OPERATORS:-0}
    REMAINDER=$((OPERANDS - OPERATORS))

    if [ "$OPERANDS" -eq 0 ] && [ "$OPERATORS" -eq 0 ]; then
        echo "✔ <$TAG_NAME> is empty"
        continue
    fi
    if [ "$OPERANDS" -eq 0 ]; then
        echo "❌ Error in <$TAG_NAME>: Must contain at least one operand."
          PIPELINE_FAILED=$PIPELINE_FAILED+1
    elif [ "$REMAINDER" -ne 1 ]; then
        echo "❌ Error in <$TAG_NAME>: Leaves $REMAINDER items on the stack instead of 1."
        echo "   Details: Found $OPERANDS operands and $OPERATORS operators."
        PIPELINE_FAILED=$PIPELINE_FAILED+1
    else
        echo "✔ <$TAG_NAME> passed."
    fi
done

exit $PIPELINE_FAILED

