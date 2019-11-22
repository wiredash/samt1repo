var AWS = require('aws-sdk');
var threshold = 0.005;
const axios = require('axios');

async function log_parsing_result(data){
  const url = 'https://czicmktc8a.execute-api.us-east-1.amazonaws.com/invoicestatus/';
  
 const req = await axios.post(
   url,
   data,
   { headers: { 'Content-Type': 'application/json' } }
  ).catch(e=>console.log(e));
  console.log(req);
    
}


function itemExtract(arr){
    const itemList = arr.filter(function(item){
        return item['PRICE ']!=='' && !isNaN(item['PRICE ']);
    });
    return itemList;
    
}
function removeDuplicates(dedupeArr) {
 return dedupeArr.reduce((accumulator, item, index, array) => {
  const { list, hashList } = accumulator;
  const hash = JSON.stringify(item).replace(/\s/g, '');
  if (hash && !hashList.includes(hash)) {
    hashList.push(hash);
    list.push(item);
  }
  if (index + 1 !== array.length) {
    return accumulator;
  }  else {
    return accumulator.list;
  }
}, { list: [], hashList: [] });
}
function escapeSpecialChars(jsonString) {
    return jsonString.replace(/\n/g, "\\n")
        .replace(/\r/g, "\\r")
        .replace(/\t/g, "\\t")
        .replace(/\f/g, "\\f");
}
function selectByAreaWithStartEndText(entryText, exitText, left, top, right, lineArray, fromPage){
    let exitTriggerText=exitText;
    let startBillTo = false;
    const textInSelection = lineArray.filter(function(item) {
        //Find me everything for a rectangle for Bill To
        if(item.line==entryText) startBillTo=true;
        if(item.boundingBox.Left>left
          && item.boundingBox.Top<top
          && item.boundingBox.Width+item.boundingBox.Left<right
          && exitTriggerText==exitText
          && startBillTo
          && item.page==fromPage
            ){
            if(item.line==exitTriggerText) exitTriggerText='';
            return item;
        }
    });
    return textInSelection;
}
function findWithAttr(array, attr, value) {
    for(var i = 0; i < array.length; i += 1) {
        if(array[i][attr] === value) {
            return i;
        }
    }
    return -1;
}

function getNextItem(lineArray, searchText, fromPage){
  const pageLines = lineArray.filter((item)=>item.page==fromPage)
  const indexOfSearchText = findWithAttr(pageLines,"line",searchText)
  if(indexOfSearchText>0){
    
    // if(indexOfSearchText==1){
    // console.log("ASH FOUND43343",indexOfSearchText)
    // const prevPageLines = lineArray.filter((item)=>item.page==fromPage)
    // console.log(prevPageLines)
    // return prevPageLines[prevPageLines.length-1].line
    // }
    return pageLines[indexOfSearchText-1].line
  }else{
    return "not found"
  }
}
function getMasterTotalText(lineArray, fromPage){
  console.log("FinalPage:", fromPage)
  return lineArray.filter(function(item){
    let firstItem = true;
    if(item.line.match("^MASTER IN") && firstItem){ //"MASTER INVOICE TOTALS")
        firstItem=false;
        return item;
    }
  });
}

function getTaxLines(lineArray, fromPage){
  let HSTAmount = getNextItem(lineArray, "HST", fromPage)
  if(HSTAmount=="not found") getNextItem(lineArray, "HST", fromPage+1)
  HSTAmount = (isNaN(HSTAmount)) ? "0" : HSTAmount
  
  
  let GSTAmount = getNextItem(lineArray, "GST", fromPage)
  GSTAmount = (isNaN(GSTAmount)) ? "0" : GSTAmount
  // if(GSTAmount=="not found") getNextItem(lineArray, "GST", fromPage-1)
  
  let QSTAmount = getNextItem(lineArray, "QST", fromPage)
  QSTAmount = (isNaN(QSTAmount)) ? "0" : QSTAmount
  // if(QSTAmount=="not found") getNextItem(lineArray, "QST", fromPage-1)  
  // for (var i=lineArray.length-1; i>=0; i--) if(lineArray[i].line.match("^GST")) break;
  // let GSTLines = lineArray[i+1];
  // GSTLines.page = GSTLines.page.toString();
  // // console.log("GSTLINES:", GSTLines.page.toString());
  // for (var i=lineArray.length-1; i>=0; i--) if(lineArray[i].line.match("^HST")) break;
  // let HSTLines = lineArray[i+1];
  // HSTLines.page = HSTLines.page.toString();

  
  // for (var i=lineArray.length-1; i>=0; i--) if(lineArray[i].line.match("^QST")) break;
  // let QSTLines = lineArray[i+1];    
  // QSTLines.page = QSTLines.page.toString();
  
  // i = 0;
  // for(i; i == ii; i--) if(lineArray[ii].line.match("^GST")) break;
  // const GSTLines = lineArray[ii+1];   

  return  { "taxLines":  [
           {"HST": HSTAmount},
           {"QST": QSTAmount},       
           {"GST": GSTAmount}
          ] }
}


function selectOneTextFromBoundingBox(left, top, bottom, right, lineArray, fromPage){
  return lineArray.filter(function(item){
    let firstItem = true;
    if(item.boundingBox.Left>left
    && item.boundingBox.Top>top
    && item.boundingBox.Top+item.boundingBox.Height<bottom
    && firstItem
    && item.boundingBox.Left+item.boundingBox.Width<right
    && item.page==fromPage
      ){
        firstItem=false;
        return item;
    }
  });
}
function selectOneTextFromABSBoundingBox(width, height, left, top, lineArray, fromPage){
  const filteredArr = lineArray.filter(function(item){
    let firstItem = true;
    if(Math.abs(item.boundingBox.Left-left)<threshold
    && Math.abs(item.boundingBox.Top-top)<threshold
    // && Math.abs(item.boundingBox.Width-width)<threshold
    && firstItem
    // && Math.abs(item.boundingBox.Height-height)<threshold
    && item.page==fromPage
      ){
        firstItem=false;
        return item;
    }
  });
//   console.log(filteredArr);
  const val = removeDuplicates(filteredArr);
  //if(val!==undefined){
  if(val!==undefined && val.length>0){
    return val[0].line;
  } else {
    return false;
  }
}

// function selectOneTextFromABSBoundingBox2(width, height, left, top, lineArray, fromPage){
//   const filteredArr = lineArray.filter(function(item){
//     let firstItem = true;
//     if(Math.abs(item.boundingBox.Left-left)<threshold
//     && Math.abs(item.boundingBox.Top-top)<threshold
//     // && Math.abs(item.boundingBox.Width-width)<threshold
//     && firstItem
//     // && Math.abs(item.boundingBox.Height-height)<threshold
//     && item.page==fromPage
//       ){
//         firstItem=false;
//         return item;
//     }
//   });
// //   console.log(filteredArr);
//   const val = removeDuplicates(filteredArr);
//   //if(val!==undefined){
//   if(val!==undefined && val.length>0) {
//     console.log("TOTAL Value", val)
//     return val[0].line;
//   } else {
//     return false;
//   }
// }



exports.handler = async (event) => {
    const inputString = escapeSpecialChars(JSON.stringify(event.body));
    var inputDataVal = JSON.parse(inputString);
    var bucketName = inputDataVal.bucket;
    var keyName = inputDataVal.key.replace(/\"/g, '');
    var params = {Bucket: bucketName, Key: keyName};
    var s3 = new AWS.S3();
    const fileData = await s3.getObject(params).promise();
    var inputData = JSON.parse(JSON.stringify(fileData.Body.toString('utf-8')));
    var inputJson = JSON.parse(inputData);
    
    const invetag = inputJson.InvoiceHeader.etag;
    console.log(invetag);
    //console.log(inputJson.InvoiceHeader);
    
    //This is the key JSON variable for Invoice Header Info
    var invoiceLineData = inputJson.invoiceLines;
    //console.log(invoiceLineData);
// "Width":0.16330420970916748, "Height":0.01293734647333622,  "Left":0.041104622185230255, "Top":0.22838656604290009
    const billTo = selectOneTextFromABSBoundingBox(0.16, 0.012, 0.0411, 0.22838, invoiceLineData, 1);
     console.log("Bill To:", billTo);
// "Width":0.11482591181993484, "Height":0.013354707509279251, "Left":0.0409310907125473, "Top":0.24853374063968658
    const billToAddressLine1 = selectOneTextFromABSBoundingBox(0.114, 0.013, 0.0409, 0.2485, invoiceLineData, 1);
    console.log("Address Line 1:", billToAddressLine1);
// "Width":0.05689051002264023, "Height":0.012759076431393623, "Left":0.04080550745129585, "Top":0.3028721213340759
    const billToAddressCity = selectOneTextFromABSBoundingBox(0.056, 0.012, 0.0408, 0.3028, invoiceLineData, 1);
    // console.log("Address City:", billToAddressCity);
// "Width":0.01702551729977131, "Height":0.012923464179039001, "Left":0.19714447855949402, "Top":0.3030284643173218
    const billToAddressState = selectOneTextFromABSBoundingBox(0.017, 0.012, 0.197, 0.303, invoiceLineData, 1);
    // console.log("Address State:", billToAddressState);
// {  "Width":0.05655677989125252, "Height":0.01238803006708622,"Left":0.04124880209565163,"Top":0.3239869177341461 }
    const billToAddressZip = selectOneTextFromABSBoundingBox(0.056, 0.012, 0.0412, 0.323, invoiceLineData, 1);
    // console.log("Address PostalCode:", billToAddressZip);
// {  "Width":0.024180835112929344, "Height":0.013079427182674408, "Left":0.19698692858219147,"Top":0.3238945007324219 }
    const billToAddressCountry = selectOneTextFromABSBoundingBox(0.024, 0.013, 0.196, 0.323, invoiceLineData, 1);
    // console.log("Address Country:", billToAddressCountry);
// {  "Width":0.04380112141370773, "Height":0.014226121827960014, "Left":0.4867849349975586,"Top":0.2732027769088745 }
    const customerOrderReference = selectOneTextFromABSBoundingBox(0.043, 0.014, 0.4867, 0.273, invoiceLineData, 1);
    console.log("Customer Order Reference:", customerOrderReference);
    //*******INVOICE NUMBER START
    //const invoiceNumber = selectOneTextFromBoundingBox(0.709, 0.129, 0.146, 0.754, invoiceLineData, 1)[0].line;
    
    const invoiceNumber = selectOneTextFromABSBoundingBox(0.0425, 0.0149, 0.7091, 0.1280, invoiceLineData, 1);
    console.log("InvoiceNo", invoiceNumber)
    //const invoiceNumber = selectOneTextFromBoundingBox(0.708, 0.129, 0.146, 0.756, invoiceLineData, 1)[0].line;
    // console.log("Invoice Number", invoiceNumber);
    //*******INVOICE NUMBER END
    //Due date
    // const dueDate = selectOneTextFromBoundingBox(0.829, 0.171, 0.185, 0.789, invoiceLineData, 1);
// {"Width": 0.05076748877763748, "Height": 0.014736424200236797, "Left": 0.829365611076355, "Top": 0.17102663218975067}
    const reverseInvoiceLineData = invoiceLineData.reverse();
    const dueDate = selectOneTextFromABSBoundingBox(0.05, 0.014, 0.829, 0.171, invoiceLineData, 1);
    // console.log("Due date:", dueDate);
    const masterTotalTextTable = getMasterTotalText(invoiceLineData, reverseInvoiceLineData[0].page);
    //console.log("Master Total Text Table:",  masterTotalTextTable);
    // const masterTotalText =  masterTotalTextTable[masterTotalTextTable.length-1];
    var masterTotalText = getNextItem(invoiceLineData, "MASTER INVOICE TOTALS", reverseInvoiceLineData[0].page).replace("$","").replace(",","")
    if(masterTotalText=="not found"){
       masterTotalText = getNextItem(invoiceLineData, "MASTER INVPICE TOTALS", reverseInvoiceLineData[0].page).replace("$","").replace(",","")
    }
    console.log("Master Total Text:",  masterTotalText);
    // console.log("Table Length", masterTotalTextTable.length)
    
    // const invoiceTotalTable = selectOneTextFromABSBoundingBox(0.064, 0.017, 0.860, masterTotalText.boundingBox.Top, invoiceLineData, reverseInvoiceLineData[0].page)//.replace("$", "").replace(",",""); //T, L
    // console.log(invoiceTotalTable);
    // var invoiceTotalTable;
    
    // var i;
    // for (i = 0; i < masterTotalTextTable.length; i++) {
    //   invoiceTotalTable = selectOneTextFromABSBoundingBox(0.069, 0.016, 0.850, masterTotalText.boundingBox.Top, invoiceLineData, i);
    //   if(invoiceTotalTable!==undefined && invoiceTotalTable.length>0) {
    //       invoiceTotalTable = invoiceTotalTable.replace("$", "").replace(",",""); //T, L
    //     break;  
    //   }
    //   //invoiceTotalTable = selectOneTextFromABSBoundingBox(0.064, 0.017, 0.860, masterTotalText.boundingBox.Top, invoiceLineData, i)
    //   console.log("Total", invoiceTotalTable)
    // }
    
    //const invoiceTotalTable = selectOneTextFromABSBoundingBox2(0.069, 0.016, 0.850, masterTotalText.boundingBox.Top, invoiceLineData, 34).replace("$", "").replace(",",""); //T, L
    // const invoiceTotal = selectOneTextFromABSBoundingBox(0.0648, 0.0170, 0.8600, 0.7401, invoiceLineData, 1); //T, L
    // console.log("Invoice Total:", invoiceTotalTable );
    
    let invoiceItemArray = [];
    let invoiceItemObj = {};
    let prevStore = '';
    let prevInvNo = ''; 
    let currentStore = '';
    let currentInvNo = '';    
    const invLineItems = itemExtract(inputJson.InvoiceItems);

    
    // invLineItems.map((item)=>{
    //     currentStore = item[Object.keys(item)[0]];
    //     if(currentStore==''){ 
    //         currentStore = prevStore;
    //     }
    //     prevStore = currentStore;

    //     currentInvNo = item['INVOICE/ '];
    //     if (currentInvNo== ''){
    //         currentInvNo = prevInvNo;
    //     }
    //     prevInvNo = currentInvNo;
        
    //     const desc = 'Store:' + currentStore + ' Inv No:' + currentInvNo + ' Prd. Code:' + item['PRODUCT CODE '];
        
    //     invoiceItemObj.description = desc;
    //     invoiceItemObj = {}
    //     invoiceItemObj.quantity = item['UNITS SHIPPED '];
    //     invoiceItemObj.price = item['PRICE '];
    //     invoiceItemObj.subTotal = invoiceItemObj.price * invoiceItemObj.quantity; //item['SUB-TOTAL/ '];
    //     invoiceItemObj.subTotal = invoiceItemObj.subTotal.toString();
    //     invoiceItemArray.push(invoiceItemObj);
    // });
    
    const tDueDate = new Date(dueDate).getTime();
    
    // const invoiceItemsTotal
    
    const invoiceObject = {
        "etag" : inputDataVal.etag,
        "file" : inputDataVal.file,
        "s3bucket" : inputDataVal.s3bucket,
        "invoiceNumber": invoiceNumber,
        "customerBillTo": billTo,
        "dueDate": tDueDate,
        "description": "Order Reference: " + customerOrderReference, 
        // "invoiceItems": invoiceItemArray,
        "invoiceTaxLines": getTaxLines(reverseInvoiceLineData, reverseInvoiceLineData[0].page),
        "invoiceTotalAmount": masterTotalText
    };
    

    // invoiceObject.etag = invetag;
    
    // console.log(invoiceObject);
    // const keyNameParsed = keyName + '_apay_converted.json'
    // s3 = new AWS.S3({apiVersion: '2006-03-01'});
    // var fileParams = {
    //             Bucket : bucketName,
    //             Key : keyNameParsed,
    //             Body : invoiceObject
    //         };   
    //     s3.putObject(params, function(err, data) {
    //       if (err) console.log(err, err.stack); // an error occurred
    //       else     console.log(data);           // successful response
    //     });
    const id = 'invoice:' + invetag;
    const statusDetails = {
      bufferData: invoiceObject.invoiceTotalAmount,
      stateData: invoiceObject
    };
    const statusData = {
      invoiceId: id,
      nextState: "ANALYZED",
      stateData: statusDetails
    };
    await log_parsing_result(statusData);
    
    const response = {
        statusCode: 200,
        body: invoiceObject
        , 
    };
    return response;
};


