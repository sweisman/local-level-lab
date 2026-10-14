// Text, navigation and code remain readable if either browser library fails.
window.MathJax={tex:{inlineMath:[["\\(","\\)"]],displayMath:[["\\[","\\]"]]},options:{skipHtmlTags:["script","noscript","style","textarea","pre","code"]}};
if(document.querySelector(".math")){
  const math=document.createElement("script");
  math.src="https://cdn.jsdelivr.net/npm/mathjax@3.2.2/es5/tex-mml-chtml.js";
  math.async=true;document.head.appendChild(math);
}
if(document.querySelector("code.language-mermaid")){
  import("https://cdn.jsdelivr.net/npm/mermaid@11.12.0/dist/mermaid.esm.min.mjs").then(async({default:mermaid})=>{
    mermaid.initialize({startOnLoad:false,securityLevel:"strict",theme:"neutral"});
    for(const code of document.querySelectorAll("code.language-mermaid")){
      const drawing=document.createElement("div");drawing.className="mermaid";drawing.textContent=code.textContent;
      code.parentElement.insertAdjacentElement("afterend",drawing);
      try{await mermaid.run({nodes:[drawing]});code.parentElement.remove();}
      catch{drawing.remove();}
    }
  }).catch(()=>{});
}
