import React, { useState, useEffect } from 'react';

const Comp2 = () => {
    const [input, setInput] = useState("");
    const [result, setResult] = useState("");

    const handleClick = (value) => {
        if (value === "=") {
            try {
                setResult(eval(input)); // Evaluate the expression
            } catch {
                setResult("Error");
            }
        } else if (value === "C") {
            setInput("");
            setResult("");
        } else {
            setInput(input + value);
        }
    };

    const handleKeyPress = (e) => {
        const key = e.key;
        if (key === "Enter") {
            handleClick("=");
        } else if (key === "Escape") {
            handleClick("C");
        } else if (/^[0-9+\-*/.]$/.test(key)) {
            handleClick(key);
        }
    };

    useEffect(() => {
        window.addEventListener("keydown", handleKeyPress);
        return () => {
            window.removeEventListener("keydown", handleKeyPress);
        };
    }, [input]);

    return (
        <div style={containerStyle}>
            <div style={displayStyle}>
                <input
                    type="text"
                    value={input}
                    readOnly
                    style={inputStyle}
                />
                <input
                    type="text"
                    value={result}
                    readOnly
                    style={resultStyle}
                />
            </div>
            <div style={buttonContainerStyle}>
                {buttons.map((button) => (
                    <button
                        key={button}
                        onClick={() => handleClick(button)}
                        style={buttonStyle(button)}
                    >
                        {button}
                    </button>
                ))}
            </div>
        </div>
    );
};

const buttons = [
    "C", "7", "8", "9", "/",
    "4", "5", "6", "*",
    "1", "2", "3", "-",
    "0", ".", "=", "+"
];

const containerStyle = {
    maxWidth: "250px",
    margin: "20px auto",
    border: "2px solid #333",
    borderRadius: "12px",
    boxShadow: "0 4px 8px rgba(0, 0, 0, 0.2)",
    padding: "10px",
    backgroundColor: "#fafafa"
};

const displayStyle = {
    marginBottom: "10px"
};

const inputStyle = {
    width: "calc(100% - 20px)",
    padding: "10px",
    border: "1px solid #ccc",
    borderRadius: "8px",
    marginBottom: "5px",
    textAlign: "right",
    fontSize: "18px",
    backgroundColor: "#fff",
    color: "#000", // Set text color to black
    boxSizing: "border-box"
};

const resultStyle = {
    width: "calc(100% - 20px)",
    padding: "10px",
    border: "1px solid #ccc",
    borderRadius: "8px",
    textAlign: "right",
    fontSize: "18px",
    backgroundColor: "#e8e8e8",
    color: "#000", // Set text color to black
    boxSizing: "border-box"
};

const buttonContainerStyle = {
    display: "grid",
    gridTemplateColumns: "repeat(4, 1fr)",
    gap: "8px"
};

const buttonStyle = (button) => ({
    padding: "16px",
    fontSize: "18px",
    border: "none",
    borderRadius: "8px",
    backgroundColor: button === "=" ? "#4caf50" : 
                        button === "C" ? "#f44336" :
                        "#f1f1f1",
    color: button === "=" || button === "C" ? "#fff" : "#333",
    cursor: "pointer",
    transition: "background-color 0.3s, box-shadow 0.3s",
    boxShadow: "0 2px 4px rgba(0, 0, 0, 0.2)",
    outline: "none",
    fontWeight: "bold",
    textAlign: "center"
});

export default Comp2;
