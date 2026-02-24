import React, { useState, useMemo } from 'react';
import { usePaintStore, Product } from './paintStore';
import { Calculator, ShoppingCart, Trash2, Target, DollarSign, Activity, ShieldCheck, Plus } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { createOrder, generateInvoice, downloadInvoicePdf } from './api/invoiceApi';

const DEFAULT_STATE_CODE = '37'; // A.P.

export const Billing = () => {
  const products = usePaintStore((state) => state.products) ?? [];
  const addSale = usePaintStore((state) => state.addSale);
  const [cart, setCart] = useState<{ product: Product; quantity: number }[]>([]);
  const [selectedProductId, setSelectedProductId] = useState('');
  const [quantity, setQuantity] = useState(1);
  const [customer, setCustomer] = useState({
    name: '',
    address: '',
    gstin: '',
    phone: '',
    state_code: DEFAULT_STATE_CODE,
  });
  const [isSubmitting, setIsSubmitting] = useState(false);

  const activeProduct = useMemo(() =>
    products.find(p => p.id === selectedProductId),
    [products, selectedProductId]
  );

  const calculateItemTotals = (product: Product, qty: number) => {
    const baseDpValue = product.dp * qty;
    const billDiscountAmount = (baseDpValue * product.billPercent) / 100;
    const afterBillDiscount = baseDpValue - billDiscountAmount;
    const cdDiscountAmount = (afterBillDiscount * product.cdPercent) / 100;
    const afterCdDiscount = afterBillDiscount - cdDiscountAmount;
    const gstAmount = (afterCdDiscount * product.gstPercent) / 100;
    const totalAmount = afterCdDiscount + gstAmount;

    return {
      baseDpValue,
      billDiscountAmount,
      cdDiscountAmount,
      gstAmount,
      totalAmount,
      totalLiters: product.litersPerCan * qty
    };
  };

  const cartTotals = useMemo(() => {
    return cart.reduce((acc, item) => {
      const totals = calculateItemTotals(item.product, item.quantity);
      return {
        baseTotal: acc.baseTotal + totals.baseDpValue,
        totalDiscount: acc.totalDiscount + totals.billDiscountAmount + totals.cdDiscountAmount,
        totalGst: acc.totalGst + totals.gstAmount,
        netTotal: acc.netTotal + totals.totalAmount,
        totalLiters: acc.totalLiters + totals.totalLiters
      };
    }, { baseTotal: 0, totalDiscount: 0, totalGst: 0, netTotal: 0, totalLiters: 0 });
  }, [cart]);

  const addToCart = () => {
    if (!activeProduct || quantity <= 0) return;
    if (quantity > activeProduct.quantity) {
      alert("Insufficient operational units available.");
      return;
    }

    setCart(prev => {
      const existingIndex = prev.findIndex(item => item.product.id === activeProduct.id);
      if (existingIndex > -1) {
        const newCart = [...prev];
        newCart[existingIndex].quantity += quantity;
        return newCart;
      }
      return [...prev, { product: activeProduct, quantity }];
    });

    setSelectedProductId('');
    setQuantity(1);
  };

  const removeFromCart = (productId: string) => {
    setCart(prev => prev.filter(item => item.product.id !== productId));
  };

  const handleCommit = async () => {
    if (cart.length === 0) return;
    const trimmedName = customer.name.trim();
    if (!trimmedName) {
      alert('Please enter customer name (Sri.) before committing.');
      return;
    }

    setIsSubmitting(true);
    try {
      // Build order items: amount = taxable value (after discounts, before GST)
      const items = cart.map((item, idx) => {
        const totals = calculateItemTotals(item.product, item.quantity);
        const taxableAmount = totals.totalAmount - totals.gstAmount; // after discounts, before GST
        const rate = taxableAmount / item.quantity;
        return {
          sno: idx + 1,
          description: item.product.name,
          hsn_sac: '998313',
          quantity: item.quantity,
          rate: Math.round(rate * 100) / 100,
          amount: Math.round(taxableAmount * 100) / 100,
        };
      });

      const { order_id } = await createOrder({
        customer: {
          name: trimmedName,
          address: customer.address.trim() || undefined,
          gstin: customer.gstin.trim() || undefined,
          phone: customer.phone.trim() || undefined,
          state_code: customer.state_code.trim() || DEFAULT_STATE_CODE,
        },
        items,
      });

      const { invoice_no } = await generateInvoice(order_id);

      // Save to local store for History
      cart.forEach(item => {
        const totals = calculateItemTotals(item.product, item.quantity);
        addSale({
          productId: item.product.id,
          productName: item.product.name,
          quantitySold: item.quantity,
          litersPerCan: item.product.litersPerCan,
          ratePerCan: item.product.dp,
          totalLiters: totals.totalLiters,
          totalAmount: totals.totalAmount,
          calculations: {
            baseDp: totals.baseDpValue,
            billDiscountAmount: totals.billDiscountAmount,
            cdDiscountAmount: totals.cdDiscountAmount,
            gstAmount: totals.gstAmount
          }
        });
      });

      setCart([]);

      // Download PDF to user's device
      await downloadInvoicePdf(order_id, invoice_no);

      alert('Order saved and invoice downloaded successfully.');
    } catch (err) {
      const msg = err instanceof Error ? err.message : 'Failed to save order.';
      alert(`Error: ${msg}\n\nEnsure the invoice backend is running at http://127.0.0.1:8000`);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-16">
      <header className="mb-12">
        <div className="flex items-center gap-4 mb-4">
          <div className="bg-emerald-600 p-3 rounded-2xl shadow-lg shadow-emerald-500/20">
            <ShoppingCart className="text-white" size={24} />
          </div>
          <div>
            <h2 className="text-5xl font-black text-white tracking-tighter uppercase">Dispatch <span className="text-emerald-500 font-serif italic italic lowercase tracking-tight">Terminal</span></h2>
            <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.4em] mt-2">Inventory Outbound & Fiscal Commitment</p>
          </div>
        </div>
      </header>

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-16">
        {/* Product Selection */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          className="xl:col-span-1"
        >
          <div className="glass-card p-10 rounded-[3rem] sticky top-32 border-white/10 relative overflow-hidden">
            <div className="absolute top-0 right-0 p-8">
              <Target size={20} className="text-emerald-500/20" />
            </div>
            <h3 className="text-xl font-black text-white mb-10">Select Unit For Dispatch</h3>

            <div className="space-y-8">
              <div className="space-y-3">
                <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Asset Identity</label>
                <select
                  value={selectedProductId}
                  onChange={(e) => setSelectedProductId(e.target.value)}
                  className="elite-input appearance-none bg-slate-900 border-white/10"
                >
                  <option value="" className="bg-slate-900">-- SELECT ASSET --</option>
                  {products.map(p => (
                    <option key={p.id} value={p.id} className="bg-slate-900">
                      {p.name} ({p.quantity} IN STOCK)
                    </option>
                  ))}
                </select>
              </div>

              <AnimatePresence>
                {activeProduct && (
                  <motion.div
                    initial={{ opacity: 0, height: 0 }}
                    animate={{ opacity: 1, height: 'auto' }}
                    exit={{ opacity: 0, height: 0 }}
                    className="space-y-6"
                  >
                    <div className="p-6 bg-emerald-500/5 rounded-3xl border border-emerald-500/20">
                      <div className="flex justify-between items-center mb-4">
                        <span className="text-[10px] font-black text-emerald-500 uppercase tracking-widest">Base Analysis</span>
                        <span className="text-xs font-bold text-white">READY</span>
                      </div>
                      <div className="grid grid-cols-2 gap-4">
                        <div>
                          <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Unit DP</p>
                          <p className="text-lg font-black text-white">₹{activeProduct.dp}</p>
                        </div>
                        <div>
                          <p className="text-[9px] font-black text-slate-500 uppercase tracking-widest">Volume</p>
                          <p className="text-lg font-black text-white">{activeProduct.litersPerCan}L</p>
                        </div>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <label className="text-[10px] font-black text-slate-500 uppercase tracking-widest ml-1">Payload Quantity</label>
                      <input
                        type="number"
                        min="1"
                        className="elite-input"
                        value={quantity}
                        onChange={(e) => setQuantity(Math.max(1, Number(e.target.value)))}
                      />
                    </div>

                    <button
                      onClick={addToCart}
                      className="elite-button-success w-full"
                    >
                      <Plus size={20} />
                      Stage For Dispatch
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          </div>
        </motion.div>

        {/* Cart & Billing Analysis */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          className="xl:col-span-2 space-y-10"
        >
          <div className="glass-card rounded-[3.5rem] bg-slate-900/60 overflow-hidden border-white/10">
            <div className="p-8 bg-slate-950 flex justify-between items-center text-white border-b border-white/5">
              <div className="flex items-center gap-4">
                <div className="bg-emerald-600/20 p-2.5 rounded-xl border border-emerald-500/30">
                  <Activity size={20} className="text-emerald-400" />
                </div>
                <h3 className="text-sm font-black uppercase tracking-[0.2em]">Live Dispatch Analysis</h3>
              </div>
              <div className="px-5 py-2.5 bg-indigo-500/10 rounded-full border border-indigo-500/20 flex items-center gap-3">
                <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full animate-pulse"></div>
                <span className="text-[10px] font-black uppercase tracking-widest text-indigo-400">{cart.length} Payload Items Staged</span>
              </div>
            </div>

            <div className="p-4">
              <AnimatePresence mode="popLayout">
                {cart.map((item) => (
                  <motion.div
                    key={item.product.id}
                    layout
                    initial={{ opacity: 0, x: 20 }}
                    animate={{ opacity: 1, x: 0 }}
                    exit={{ opacity: 0, x: -20 }}
                    className="p-8 bg-white/5 rounded-[2.5rem] border border-white/5 mb-4 group hover:bg-white/10 transition-all"
                  >
                    <div className="flex flex-col md:flex-row justify-between gap-8">
                      <div className="flex items-center gap-6">
                        <div className="w-16 h-16 bg-slate-950 rounded-2xl flex items-center justify-center text-emerald-400 font-black text-2xl border border-emerald-500/20">
                          {item.product.name?.charAt(0) || 'Ø'}
                        </div>
                        <div>
                          <h4 className="font-black text-xl text-white uppercase tracking-tight">{item.product.name}</h4>
                          <p className="text-[10px] font-black text-slate-500 uppercase tracking-widest mt-1">
                            {item.quantity} Unit(s) • {item.product.litersPerCan * item.quantity} Liters Total
                          </p>
                        </div>
                      </div>

                      <div className="flex flex-col md:flex-row items-center gap-10">
                        <div className="text-right">
                          <p className="text-[9px] font-black text-slate-600 uppercase tracking-widest">Commit Amount</p>
                          <p className="text-2xl font-black text-white tabular-nums tracking-tighter">
                            ₹{calculateItemTotals(item.product, item.quantity).totalAmount.toLocaleString()}
                          </p>
                        </div>
                        <button
                          onClick={() => removeFromCart(item.product.id)}
                          className="p-4 bg-red-500/10 text-red-500 hover:bg-red-500 hover:text-white rounded-2xl transition-all border border-red-500/20"
                        >
                          <Trash2 size={20} />
                        </button>
                      </div>
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>

              {cart.length === 0 && (
                <div className="py-32 text-center">
                  <div className="w-24 h-24 bg-white/5 rounded-[2.5rem] flex items-center justify-center mx-auto mb-8 border border-white/10">
                    <Calculator size={48} className="text-slate-700" />
                  </div>
                  <h4 className="text-xl font-black text-white mb-2 uppercase">Analysis Void</h4>
                  <p className="text-slate-500 font-extrabold uppercase tracking-[0.3em] text-[10px]">Await Stage Deployment</p>
                </div>
              )}
            </div>
          </div>

          {cart.length > 0 && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              className="glass-card p-12 rounded-[3.5rem] bg-slate-900 border-emerald-500/30 shadow-[0_40px_80px_-20px_rgba(16,185,129,0.3)]"
            >
              <h3 className="text-2xl font-black text-white mb-10 uppercase tracking-tighter flex items-center gap-4">
                <DollarSign className="text-emerald-500" />
                Fiscal Commit Manifest
              </h3>

              {/* Customer Details (Billed To) */}
              <div className="mb-10 p-6 bg-slate-950/60 rounded-2xl border border-white/5">
                <h4 className="text-[10px] font-black text-slate-500 uppercase tracking-widest mb-4">Details of Receiver (Billed To)</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="text-[9px] font-black text-slate-500 uppercase tracking-widest block mb-2">Sri. (Name) *</label>
                    <input
                      type="text"
                      value={customer.name}
                      onChange={(e) => setCustomer(c => ({ ...c, name: e.target.value }))}
                      placeholder="Customer name"
                      className="elite-input w-full"
                    />
                  </div>
                  <div>
                    <label className="text-[9px] font-black text-slate-500 uppercase tracking-widest block mb-2">Cell</label>
                    <input
                      type="text"
                      value={customer.phone}
                      onChange={(e) => setCustomer(c => ({ ...c, phone: e.target.value }))}
                      placeholder="Phone number"
                      className="elite-input w-full"
                    />
                  </div>
                  <div className="md:col-span-2">
                    <label className="text-[9px] font-black text-slate-500 uppercase tracking-widest block mb-2">Address</label>
                    <input
                      type="text"
                      value={customer.address}
                      onChange={(e) => setCustomer(c => ({ ...c, address: e.target.value }))}
                      placeholder="Full address"
                      className="elite-input w-full"
                    />
                  </div>
                  <div>
                    <label className="text-[9px] font-black text-slate-500 uppercase tracking-widest block mb-2">GSTIN</label>
                    <input
                      type="text"
                      value={customer.gstin}
                      onChange={(e) => setCustomer(c => ({ ...c, gstin: e.target.value }))}
                      placeholder="GSTIN (optional)"
                      className="elite-input w-full"
                    />
                  </div>
                  <div>
                    <label className="text-[9px] font-black text-slate-500 uppercase tracking-widest block mb-2">State Code</label>
                    <input
                      type="text"
                      value={customer.state_code}
                      onChange={(e) => setCustomer(c => ({ ...c, state_code: e.target.value }))}
                      placeholder="37 for A.P."
                      className="elite-input w-full"
                    />
                  </div>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-16">
                <div className="space-y-6">
                  <div className="flex justify-between items-center py-4 border-b border-white/5">
                    <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">Base DP Valuation</span>
                    <span className="font-black text-white">₹{cartTotals.baseTotal.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between items-center py-4 border-b border-white/5">
                    <span className="text-[10px] font-black text-emerald-500 uppercase tracking-widest">System Discounts Applied</span>
                    <span className="font-black text-emerald-500">-₹{cartTotals.totalDiscount.toLocaleString()}</span>
                  </div>
                  <div className="flex justify-between items-center py-4 border-b border-white/5">
                    <span className="text-[10px] font-black text-slate-500 uppercase tracking-widest">GST (Integrated Tax)</span>
                    <span className="font-black text-white">₹{cartTotals.totalGst.toLocaleString()}</span>
                  </div>
                </div>

                <div className="flex flex-col justify-between pt-4 md:pt-0">
                  <div className="text-right mb-10">
                    <p className="text-[10px] font-black text-slate-500 uppercase tracking-[0.3em] mb-3">Total Payable Asset Value</p>
                    <p className="text-6xl font-black text-white tracking-tighter tabular-nums">
                      ₹{Math.round(cartTotals.netTotal).toLocaleString()}
                    </p>
                    <p className="text-[10px] font-black text-emerald-400 mt-4 px-4 py-2 bg-emerald-500/10 rounded-full inline-block border border-emerald-500/20">
                      MASS LOAD: {cartTotals.totalLiters.toFixed(2)} LITERS
                    </p>
                  </div>

                  <button
                    onClick={handleCommit}
                    disabled={isSubmitting}
                    className="elite-button-success h-20 text-xl shadow-[0_20px_50px_-10px_rgba(16,185,129,0.5)] disabled:opacity-60 disabled:cursor-not-allowed"
                  >
                    <ShieldCheck size={28} />
                    {isSubmitting ? 'SAVING & GENERATING...' : 'COMMIT DISPATCH & PRINT'}
                  </button>
                </div>
              </div>
            </motion.div>
          )}
        </motion.div>
      </div>
    </div>
  );
};
