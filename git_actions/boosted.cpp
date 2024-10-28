/*
CodeChecker log --build "g++ -I/usr/include boosted.cpp -lboost_system -lboost_filesystem" --output ./compile_commands.json
*/

#include <boost/optional/optional.hpp>
#include <boost/none.hpp>

class test_class
{
public:
    boost::optional<int> value_test;
    test_class(/* args */);
    ~test_class();
    // int get();
};

test_class::test_class(/* args */)
{
}

test_class::~test_class()
{
}

// int test_class::get(){
//     if (this->value_test.is_initialized())
//         return this->value_test.get();
//     else
//         return 0;    
// }

// void PutSomeData(boost::optional<test_class> &var)
// {
//     // var = test_class();
// }

//test

int main() 
{  
    boost::optional<test_class> test = boost::none;
    // PutSomeData(test); 

    if (test.get().value_test == 0)
    {
        printf("yes");
    }
    else
    {
        printf("no");
    }

    return 0;
}