import React, { useState } from 'react';

const server = process.env.API_URL || 'http://127.0.0.1:9000';

export const Listing: React.FC<{}> = () => {
  const initialState = {
    name: "",
    category: "",
    image: "",
  };
  const [values, setValues] = useState(initialState);
  const [image, setImage] = useState<File>()
  
  const onChange = (event: React.ChangeEvent<HTMLInputElement>) => {
      setValues({ ...values, [event.target.name]: event.target.value });
  };
  const getImage = (event: React.ChangeEvent<HTMLInputElement>) => {
    if (!event.target.files) return
    const img: File = event.target.files[0]
    setImage(img)
  }
  const onSubmit = (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const data = new FormData()
    if (!image) return
    data.append('name', values.name)
    data.append('category', values.category)
    data.append('image', image)

    fetch(server.concat('/items'), {
      method: 'POST',
      mode: 'cors',
      body: data,
    })
    .then(response => response.json())
    .then(data => {
      console.log('POST success:', data);
    })
    .catch((error) => {
      console.error('POST error:', error);
    })
  };
  return (
    <div className='Listing'>
      <form onSubmit={onSubmit}>
        <div>
            <input type='text' name='name' id='name' placeholder='name' onChange={onChange} required/>
            <input type='text' name='category' id='category' placeholder='category' onChange={onChange}/>
            <input type='file' name='image' id='image' placeholder='image' onChange={getImage}/>
            <button type='submit'>List this item</button>
        </div>
      </form>
    </div>

  );
}
