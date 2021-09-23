"""
Unit and regression test for the lda module.
"""

# Import package, test suite, and other packages as needed
import pytest
import torch
import numpy as np
from mlcvs.io import colvar_to_pandas
from mlcvs.lda import LDA_CV, DeepLDA_CV 

def test_lda_basins():
    """Perform LDA on 2d-basins data folder."""
    #dtype = torch.float32
    #device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Load data
    dataA = colvar_to_pandas(folder='mlcvs/data/2d-basins/',filename='COLVAR_stateA')
    dataB = colvar_to_pandas(folder='mlcvs/data/2d-basins/',filename='COLVAR_stateB')

    # Create input dataset
    xA = dataA.filter(regex='p.*').values
    xB = dataB.filter(regex='p.*').values
    names = dataA.filter(regex='p.*').columns.values
    n_features = xA.shape[1]

    # Create labels
    yA = np.zeros(len(dataA))
    yB = np.ones(len(dataB))

    X = np.concatenate([xA,xB],axis=0)
    y = np.concatenate([yA,yB],axis=0)

    # Transform to Pytorch Tensors
    #X = torch.tensor(X,dtype=dtype,device=device)
    #y = torch.tensor(y,dtype=dtype,device=device)
    
    # Define model 
    lda = LDA_CV(n_features)
    # Set features name (for PLUMED input)
    lda.set_params({'features_names': names})

    # Fit LDA
    lda.fit(X,y)

    # Project
    x_test = np.ones(2)
    y_test = lda(x_test)

    y_test = y_test.cpu()[0]
    y_test_expected = torch.tensor(-0.0960027)
    
    #ASSERT 
    print(type(y_test),type(y_test_expected))
    assert y_test_expected == y_test

    # Check PLUMED INPUT

    input = lda.plumed_input()
    expected_input = "lda_cv: COMBINE ARG=p.x,p.y COEFFICIENTS=0.657474,-0.75347 PERIODIC=NO"
    
    # ASSERT
    assert expected_input == input

@pytest.mark.slow
def test_deeplda_train():
    """Perform DeepLDA on 2d-basins data folder."""
    dtype = torch.float32
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')

    # Load data
    dataA = colvar_to_pandas(folder='mlcvs/data/2d-basins/',filename='COLVAR_stateA')
    dataB = colvar_to_pandas(folder='mlcvs/data/2d-basins/',filename='COLVAR_stateB')

    # Create input dataset
    xA = dataA.filter(regex='p.*').values
    xB = dataB.filter(regex='p.*').values
    names = dataA.filter(regex='p.*').columns.values

    # Create labels
    yA = np.zeros(len(dataA))
    yB = np.ones(len(dataB))

    # Concatenate and shuffle
    X = np.concatenate([xA,xB],axis=0)
    y = np.concatenate([yA,yB],axis=0)
    p = np.random.permutation(len(X))
    X, y = X[p], y[p]

    # Convert np to torch 
    X = torch.tensor(X,dtype=dtype,device=device)
    y = torch.tensor(y,dtype=dtype,device=device)

    ##@title Create datasets
    ntrain = 800
    nbatch =  -1
    nvalid = 200

    standardize_inputs = True #@param {type:"boolean"}

    train_data = [X[:ntrain],y[:ntrain]]
    valid_data = [X[ntrain:ntrain+nvalid],y[ntrain:ntrain+nvalid]]

    hidden_nodes = "30,30,5" #@param {type:"raw"}
    nodes = [int(x) for x in hidden_nodes.split(',')]
    nodes.insert(0, X.shape[1])
    n_hidden=nodes[-1]

    # -- Parameters --
    lrate = 0.001 #@param {type:"slider", min:0.0001, max:0.005, step:0.0001}
    lambdA = 0.05 #@param {type:"number"}
    l2_reg = 1e-5 #@param {type:"number"}
    act_reg = 2./lambdA # lorentzian regularization

    num_epochs = 100 #@param {type:"number"}
    print_loss = 1 #@param {type:"slider", min:1, max:100, step:1}
    plot_every = 5 #@param {type:"slider", min:1, max:100, step:1}
    plot_validation = True #@param {type:"boolean"}

    # MODEL
    model = DeepLDA_CV(nodes)

    #OPTIMIZER
    opt = torch.optim.Adam(model.parameters(), lr=lrate, weight_decay=l2_reg)

    # REGULARIZATION
    model.set_optimizer(opt)
    model.set_earlystopping(patience=40,min_delta=0.,consecutive=False,save_best_model=True)
    model.set_regularization(sw_reg=lambdA)#,lorentzian_reg=act_reg,)

    # TRAIN
    model.train(train_data,valid_data,info=True,log_every=10)#,batch_size=nbatch)#,nepochs=num_epochs)


if __name__ == "__main__":
    # Do something if this file is invoked on its own
    test_lda_basins()
    test_deeplda_train()