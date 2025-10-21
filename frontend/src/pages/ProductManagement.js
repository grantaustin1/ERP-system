import React, { useState, useEffect } from 'react';
import { useToast } from '../hooks/use-toast';
import { Button } from '../components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '../components/ui/dialog';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { Package, Plus, Edit, Trash2, Star, AlertTriangle } from 'lucide-react';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

export default function ProductManagement() {
  const { toast } = useToast();
  const [loading, setLoading] = useState(true);
  const [products, setProducts] = useState([]);
  const [categories, setCategories] = useState([]);
  const [productDialogOpen, setProductDialogOpen] = useState(false);
  const [categoryDialogOpen, setCategoryDialogOpen] = useState(false);
  const [editingProduct, setEditingProduct] = useState(null);
  const [editingCategory, setEditingCategory] = useState(null);
  
  const [productForm, setProductForm] = useState({
    name: '',
    sku: '',
    category_id: '',
    cost_price: '',
    markup_percent: '',
    tax_rate: '15',
    stock_quantity: '0',
    low_stock_threshold: '10',
    description: '',
    is_favorite: false
  });
  
  const [categoryForm, setCategoryForm] = useState({
    name: '',
    description: '',
    display_order: '0'
  });

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      
      const [productsRes, categoriesRes] = await Promise.all([
        fetch(`${BACKEND_URL}/api/pos/products`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`${BACKEND_URL}/api/pos/categories`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      const productsData = await productsRes.json();
      const categoriesData = await categoriesRes.json();

      setProducts(productsData.products || []);
      setCategories(categoriesData.categories || []);
    } catch (error) {
      console.error('Error fetching data:', error);
      toast({
        title: "Error",
        description: "Failed to load products",
        variant: "destructive"
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCreateProduct = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/pos/products`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          ...productForm,
          cost_price: parseFloat(productForm.cost_price),
          markup_percent: parseFloat(productForm.markup_percent),
          tax_rate: parseFloat(productForm.tax_rate),
          stock_quantity: parseInt(productForm.stock_quantity),
          low_stock_threshold: parseInt(productForm.low_stock_threshold)
        })
      });

      if (!response.ok) throw new Error('Failed to create product');

      toast({
        title: "Success",
        description: "Product created successfully",
      });

      setProductDialogOpen(false);
      setProductForm({
        name: '',
        sku: '',
        category_id: '',
        cost_price: '',
        markup_percent: '',
        tax_rate: '15',
        stock_quantity: '0',
        low_stock_threshold: '10',
        description: '',
        is_favorite: false
      });
      await fetchData();
    } catch (error) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive"
      });
    }
  };

  const handleCreateCategory = async (e) => {
    e.preventDefault();
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/pos/categories`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          ...categoryForm,
          display_order: parseInt(categoryForm.display_order)
        })
      });

      if (!response.ok) throw new Error('Failed to create category');

      toast({
        title: "Success",
        description: "Category created successfully",
      });

      setCategoryDialogOpen(false);
      setCategoryForm({
        name: '',
        description: '',
        display_order: '0'
      });
      await fetchData();
    } catch (error) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive"
      });
    }
  };

  const handleDeleteProduct = async (productId) => {
    if (!window.confirm('Delete this product?')) return;
    
    try {
      const token = localStorage.getItem('token');
      const response = await fetch(`${BACKEND_URL}/api/pos/products/${productId}`, {
        method: 'DELETE',
        headers: { Authorization: `Bearer ${token}` }
      });

      if (!response.ok) throw new Error('Failed to delete product');

      toast({
        title: "Success",
        description: "Product deleted successfully",
      });

      await fetchData();
    } catch (error) {
      toast({
        title: "Error",
        description: error.message,
        variant: "destructive"
      });
    }
  };

  const lowStockProducts = products.filter(p => p.stock_quantity <= p.low_stock_threshold);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="p-6">
      <Card>
        <CardHeader>
          <div className="flex items-center justify-between">
            <CardTitle className="flex items-center gap-2">
              <Package className="h-6 w-6" />
              Product Management
            </CardTitle>
            <div className="flex gap-2">
              <Dialog open={categoryDialogOpen} onOpenChange={setCategoryDialogOpen}>
                <DialogTrigger asChild>
                  <Button variant="outline">
                    <Plus className="h-4 w-4 mr-2" />
                    Add Category
                  </Button>
                </DialogTrigger>
                <DialogContent>
                  <DialogHeader>
                    <DialogTitle>Create Category</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleCreateCategory} className="space-y-4">
                    <div>
                      <Label>Name</Label>
                      <Input
                        value={categoryForm.name}
                        onChange={(e) => setCategoryForm({...categoryForm, name: e.target.value})}
                        required
                      />
                    </div>
                    <div>
                      <Label>Description</Label>
                      <Input
                        value={categoryForm.description}
                        onChange={(e) => setCategoryForm({...categoryForm, description: e.target.value})}
                      />
                    </div>
                    <Button type="submit" className="w-full">Create Category</Button>
                  </form>
                </DialogContent>
              </Dialog>
              
              <Dialog open={productDialogOpen} onOpenChange={setProductDialogOpen}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="h-4 w-4 mr-2" />
                    Add Product
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                  <DialogHeader>
                    <DialogTitle>Create Product</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={handleCreateProduct} className="space-y-4">
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Product Name *</Label>
                        <Input
                          value={productForm.name}
                          onChange={(e) => setProductForm({...productForm, name: e.target.value})}
                          required
                        />
                      </div>
                      <div>
                        <Label>SKU / Barcode</Label>
                        <Input
                          value={productForm.sku}
                          onChange={(e) => setProductForm({...productForm, sku: e.target.value})}
                        />
                      </div>
                    </div>
                    
                    <div>
                      <Label>Category *</Label>
                      <Select
                        value={productForm.category_id}
                        onValueChange={(value) => setProductForm({...productForm, category_id: value})}
                        required
                      >
                        <SelectTrigger>
                          <SelectValue placeholder="Select category" />
                        </SelectTrigger>
                        <SelectContent>
                          {categories.map(cat => (
                            <SelectItem key={cat.id} value={cat.id}>{cat.name}</SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                    
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <Label>Cost Price (R) *</Label>
                        <Input
                          type="number"
                          step="0.01"
                          value={productForm.cost_price}
                          onChange={(e) => setProductForm({...productForm, cost_price: e.target.value})}
                          required
                        />
                      </div>
                      <div>
                        <Label>Markup % *</Label>
                        <Input
                          type="number"
                          step="0.01"
                          value={productForm.markup_percent}
                          onChange={(e) => setProductForm({...productForm, markup_percent: e.target.value})}
                          required
                        />
                      </div>
                      <div>
                        <Label>Selling Price (R)</Label>
                        <Input
                          type="number"
                          value={
                            productForm.cost_price && productForm.markup_percent
                              ? (parseFloat(productForm.cost_price) * (1 + parseFloat(productForm.markup_percent) / 100)).toFixed(2)
                              : ''
                          }
                          disabled
                        />
                      </div>
                    </div>
                    
                    <div className="grid grid-cols-3 gap-4">
                      <div>
                        <Label>Tax Rate %</Label>
                        <Input
                          type="number"
                          step="0.01"
                          value={productForm.tax_rate}
                          onChange={(e) => setProductForm({...productForm, tax_rate: e.target.value})}
                        />
                      </div>
                      <div>
                        <Label>Stock Quantity</Label>
                        <Input
                          type="number"
                          value={productForm.stock_quantity}
                          onChange={(e) => setProductForm({...productForm, stock_quantity: e.target.value})}
                        />
                      </div>
                      <div>
                        <Label>Low Stock Alert</Label>
                        <Input
                          type="number"
                          value={productForm.low_stock_threshold}
                          onChange={(e) => setProductForm({...productForm, low_stock_threshold: e.target.value})}
                        />
                      </div>
                    </div>
                    
                    <div>
                      <Label>Description</Label>
                      <Input
                        value={productForm.description}
                        onChange={(e) => setProductForm({...productForm, description: e.target.value})}
                      />
                    </div>
                    
                    <div className="flex items-center gap-2">
                      <input
                        type="checkbox"
                        checked={productForm.is_favorite}
                        onChange={(e) => setProductForm({...productForm, is_favorite: e.target.checked})}
                        className="h-4 w-4"
                      />
                      <Label>Pin to Quick Access</Label>
                    </div>
                    
                    <Button type="submit" className="w-full">Create Product</Button>
                  </form>
                </DialogContent>
              </Dialog>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="products">
            <TabsList>
              <TabsTrigger value="products">
                Products ({products.length})
              </TabsTrigger>
              <TabsTrigger value="categories">
                Categories ({categories.length})
              </TabsTrigger>
              <TabsTrigger value="low-stock">
                Low Stock ({lowStockProducts.length})
              </TabsTrigger>
            </TabsList>
            
            <TabsContent value="products">
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {products.map(product => (
                  <Card key={product.id}>
                    <CardContent className="p-4">
                      <div className="flex justify-between items-start mb-2">
                        <div className="flex-1">
                          <h4 className="font-semibold">{product.name}</h4>
                          <p className="text-sm text-gray-500">{product.category_name}</p>
                        </div>
                        {product.is_favorite && <Star className="h-4 w-4 text-yellow-500 fill-yellow-500" />}
                      </div>
                      
                      <div className="space-y-1 text-sm mb-3">
                        <div className="flex justify-between">
                          <span className="text-gray-600">Cost:</span>
                          <span>R{product.cost_price.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Markup:</span>
                          <span>{product.markup_percent}%</span>
                        </div>
                        <div className="flex justify-between font-semibold">
                          <span>Selling Price:</span>
                          <span className="text-green-600">R{product.selling_price.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between">
                          <span className="text-gray-600">Stock:</span>
                          <Badge variant={product.stock_quantity > product.low_stock_threshold ? 'default' : 'destructive'}>
                            {product.stock_quantity}
                          </Badge>
                        </div>
                      </div>
                      
                      <div className="flex gap-2">
                        <Button size="sm" variant="outline" className="flex-1" disabled>
                          <Edit className="h-3 w-3 mr-1" />
                          Edit
                        </Button>
                        <Button
                          size="sm"
                          variant="destructive"
                          onClick={() => handleDeleteProduct(product.id)}
                        >
                          <Trash2 className="h-3 w-3" />
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>
            
            <TabsContent value="categories">
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                {categories.map(category => (
                  <Card key={category.id}>
                    <CardContent className="p-4">
                      <h4 className="font-semibold mb-2">{category.name}</h4>
                      <p className="text-sm text-gray-500 mb-2">{category.description}</p>
                      <Badge>{products.filter(p => p.category_id === category.id).length} products</Badge>
                    </CardContent>
                  </Card>
                ))}
              </div>
            </TabsContent>
            
            <TabsContent value="low-stock">
              {lowStockProducts.length === 0 ? (
                <div className="text-center py-12 text-gray-500">
                  No products with low stock
                </div>
              ) : (
                <div className="space-y-3">
                  {lowStockProducts.map(product => (
                    <div key={product.id} className="flex items-center justify-between p-4 border rounded-lg bg-red-50">
                      <div className="flex items-center gap-3">
                        <AlertTriangle className="h-5 w-5 text-red-500" />
                        <div>
                          <p className="font-semibold">{product.name}</p>
                          <p className="text-sm text-gray-600">{product.category_name}</p>
                        </div>
                      </div>
                      <div className="text-right">
                        <Badge variant="destructive">{product.stock_quantity} remaining</Badge>
                        <p className="text-xs text-gray-500 mt-1">Alert at {product.low_stock_threshold}</p>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
