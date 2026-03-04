from pathlib import Path
from typing import Optional, Dict, List
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse
from pydantic import BaseModel

app = FastAPI()
IMAGE_DIR = Path(__file__).with_name("images")
IMAGE_DIR.mkdir(exist_ok=True)

class Product(BaseModel):
    id: int
    name: str
    description: str
    icon: Optional[str] = None

class ProductCreate(BaseModel):
    name: str
    description: str

class ProductUpdate(BaseModel):
    id: Optional[int] = None
    name: Optional[str] = None
    description: Optional[str] = None
    icon: Optional[str] = None


products: Dict[int, Product] = {}
image_types: Dict[int, str] = {}
next_id = 1


@app.post("/product", response_model=Product)
def create_product(body: ProductCreate):
    global next_id
    product = Product(id=next_id, name=body.name, description=body.description)
    products[next_id] = product
    next_id += 1
    return product


@app.get("/product/{product_id}", response_model=Product)
def get_product(product_id: int):
    product = products.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@app.put("/product/{product_id}", response_model=Product)
def update_product(product_id: int, body: ProductUpdate):
    product = products.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    data = body.model_dump(exclude_unset=True)

    data.pop("id", None)
    data.pop("icon", None)

    updated = product.model_copy(update=data)
    products[product_id] = updated
    return updated


@app.delete("/product/{product_id}", response_model=Product)
def delete_product(product_id: int):
    product = products.pop(product_id, None)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if product.icon:
        Path(product.icon).unlink(missing_ok=True)
    image_types.pop(product_id, None)
    return product


@app.get("/products", response_model=List[Product])
def list_products():
    return list(products.values())


@app.post("/product/{product_id}/image", response_model=Product)
async def upload_image(product_id: int, request: Request):
    product = products.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    content = await request.body()
    if not content:
        raise HTTPException(status_code=400, detail="Empty file")

    content_type = request.headers.get("content-type", "application/octet-stream")
    ext = {
        "image/png": "png",
        "image/jpeg": "jpg",
    }.get(content_type, "bin")

    file_path = IMAGE_DIR / f"{product_id}.{ext}"
    if product.icon and Path(product.icon) != file_path:
        Path(product.icon).unlink(missing_ok=True)
    file_path.write_bytes(content)
    image_types[product_id] = content_type

    updated = product.model_copy(update={"icon": str(file_path)})
    products[product_id] = updated
    return updated


@app.get("/product/{product_id}/image")
def get_image(product_id: int):
    product = products.get(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    if not product.icon or not Path(product.icon).exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(product.icon, media_type=image_types.get(product_id, "application/octet-stream"))
