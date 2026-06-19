import React from 'react';

const withLogging = (WrappedComponent) => {
  return (props) => {
    console.log('Props:', props);
    return <WrappedComponent {...props} />;
  };
};

const Mycomp = (props) => {
  return (
    <h1>{props.name}</h1>
  );
}

const Enhancedcomp = withLogging(Mycomp);

function App() {
  return (
    <>
      <Enhancedcomp name="excelr" />
    </>
  );
}

export default App;
