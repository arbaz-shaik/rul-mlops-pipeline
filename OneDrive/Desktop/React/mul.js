this.onmessage= function(event){
    let num1 = event.data.num1;
    let num2= event.data.num2;
    let res = num1*num2;
    this.postMessage(res);
}