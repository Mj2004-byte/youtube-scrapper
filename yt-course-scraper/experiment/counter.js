 
 import React from "react";
 import { createRoot } from 'react-dom/client';
 import { useState } from "react";






 const Counter=()=>{

    const [counter,setCounter]=useState(0)
    return(
        <div>
            <span>
                counter:{counter}
            </span><br/>
            <button onClick={()=>{
                setCounter(counter+1);
            }}>
                +
            </button><br/>
            <button onClick={()=>{
                setCounter(counter-1)
            }}>
                -
            </button>
        </div>
    )
 }

 const root=createRoot(document.getElementById("root"));

 root.render(<Counter/>);

