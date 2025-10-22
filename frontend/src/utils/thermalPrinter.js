/**
 * Thermal Printer Utility for Epson ESC/POS Printers
 * Generates formatted receipt content for thermal printing
 */

export const generateThermalReceipt = (transaction, businessInfo = {}) => {
  const {
    transaction_number,
    transaction_date,
    items = [],
    member_name,
    payment_method,
    payment_reference,
    subtotal,
    tax_amount,
    discount_percent,
    discount_amount,
    total_amount,
    captured_by_name,
    notes
  } = transaction;

  const {
    business_name = 'GymAccess Hub',
    address = '123 Fitness Street',
    city = 'Johannesburg',
    phone = '+27 11 123 4567',
    vat_number = 'VAT: 1234567890'
  } = businessInfo;

  // Format date
  const date = new Date(transaction_date);
  const dateStr = date.toLocaleDateString();
  const timeStr = date.toLocaleTimeString();

  // Build receipt content with proper formatting
  let receipt = `
========================================
       ${business_name}
========================================
${address}
${city}
Tel: ${phone}
${vat_number}
========================================

Transaction #: ${transaction_number}
Date: ${dateStr}  Time: ${timeStr}
Cashier: ${captured_by_name}
${member_name ? `Member: ${member_name}` : ''}

========================================
ITEMS
========================================
`;

  // Add items
  items.forEach(item => {
    const itemName = item.product_name.padEnd(20, ' ');
    const qty = `${item.quantity}x`;
    const price = `R${item.unit_price.toFixed(2)}`;
    const itemTotal = `R${item.total.toFixed(2)}`;
    
    receipt += `${itemName}\n`;
    receipt += `  ${qty} @ ${price}`;
    
    // Show item discount if any
    if (item.item_discount_amount > 0) {
      receipt += `\n  Item Disc: -R${item.item_discount_amount.toFixed(2)}`;
    }
    
    receipt += `${itemTotal.padStart(20, ' ')}\n\n`;
  });

  receipt += `========================================\n`;
  receipt += `Subtotal:${`R${subtotal.toFixed(2)}`.padStart(29, ' ')}\n`;
  receipt += `Tax (${items[0]?.tax_rate || 15}%):${`R${tax_amount.toFixed(2)}`.padStart(30, ' ')}\n`;
  
  if (discount_amount > 0) {
    receipt += `Discount (${discount_percent}%):${`-R${discount_amount.toFixed(2)}`.padStart(22, ' ')}\n`;
  }
  
  receipt += `========================================\n`;
  receipt += `TOTAL:${`R${total_amount.toFixed(2)}`.padStart(33, ' ')}\n`;
  receipt += `========================================\n\n`;
  
  receipt += `Payment Method: ${payment_method}\n`;
  if (payment_reference) {
    receipt += `Reference: ${payment_reference}\n`;
  }
  
  if (notes) {
    receipt += `\nNotes: ${notes}\n`;
  }
  
  receipt += `\n========================================\n`;
  receipt += `     Thank you for your business!\n`;
  receipt += `          Please come again\n`;
  receipt += `========================================\n\n\n\n`;

  return receipt;
};

/**
 * Print receipt to thermal printer
 * Uses browser's print dialog which can be configured for thermal printers
 */
export const printThermalReceipt = (receiptContent) => {
  // Create a hidden iframe for printing
  const printFrame = document.createElement('iframe');
  printFrame.style.position = 'absolute';
  printFrame.style.width = '0';
  printFrame.style.height = '0';
  printFrame.style.border = 'none';
  
  document.body.appendChild(printFrame);
  
  const printDocument = printFrame.contentWindow.document;
  printDocument.open();
  printDocument.write(`
    <html>
      <head>
        <title>Receipt</title>
        <style>
          @page {
            size: 80mm auto;
            margin: 0;
          }
          body {
            font-family: 'Courier New', monospace;
            font-size: 12px;
            line-height: 1.4;
            margin: 0;
            padding: 5mm;
            width: 70mm;
          }
          pre {
            margin: 0;
            padding: 0;
            white-space: pre-wrap;
            word-wrap: break-word;
          }
        </style>
      </head>
      <body>
        <pre>${receiptContent}</pre>
      </body>
    </html>
  `);
  printDocument.close();
  
  // Wait for content to load, then print
  printFrame.contentWindow.onload = () => {
    setTimeout(() => {
      printFrame.contentWindow.print();
      setTimeout(() => {
        document.body.removeChild(printFrame);
      }, 1000);
    }, 100);
  };
};

/**
 * Download receipt as text file
 */
export const downloadReceiptAsText = (receiptContent, transactionNumber) => {
  const blob = new Blob([receiptContent], { type: 'text/plain' });
  const url = window.URL.createObjectURL(blob);
  const link = document.createElement('a');
  link.href = url;
  link.download = `receipt-${transactionNumber}.txt`;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  window.URL.revokeObjectURL(url);
};
